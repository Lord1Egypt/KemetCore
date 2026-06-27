// GebCore — 2:4 structured-sparse MAC cell (KemetCore Phase 2 RTL)
//
// The processing element of the 2:4 sparse tensor core. 2:4 sparsity keeps at
// most 2 of every contiguous group of 4 weights; the weights are pre-compressed
// to (value, index) pairs, so the hardware performs exactly one MAC per KEPT lane
// — half the work of a dense matmul. Each cycle this PE:
//   * selects one of the 4 activations in the current group of 4 using the kept
//     weight's 2-bit lane index (the 2:4 metadata),
//   * multiplies it by the kept weight value (fp32),
//   * accumulates the product into a registered fp32 running sum.
// This is exactly the golden datapath:
//     out += A[:, grp+index[s]] * value[s]      (fp32 mul, fp32 accumulate)
// (golden/geb_sparse.py sparse_matmul). Composes the cocotb-verified HapiCore
// primitives hapi_fp32_mul + hapi_fp32_add, so the arithmetic is already proven.
//
// Drive one output element by streaming the K/2 kept (value,index) pairs of a
// compressed column together with that group's 4 activations; pulse `clear` with
// the first pair and `en` for all of them. `acc` holds the fp32 result one cycle
// after the last pair.
//
// Bit-exact against golden.sparse_matmul — see tb/test_spmac.py.

module geb_spmac (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         en,         // accumulate this kept lane's product
    input  logic         clear,      // start a fresh output element (ignore old acc)
    input  logic [127:0] a_group,    // the 4 fp32 activations of the current group of 4
    input  logic [1:0]   idx,        // kept weight's lane within the group (0..3)
    input  logic [31:0]  val,        // kept weight value (fp32)
    output logic [31:0]  acc         // fp32 running accumulator (registered)
);
    // select the activation addressed by the 2:4 metadata index
    logic [31:0] a_sel;
    always_comb begin
        case (idx)
            2'd0:    a_sel = a_group[31:0];
            2'd1:    a_sel = a_group[63:32];
            2'd2:    a_sel = a_group[95:64];
            default: a_sel = a_group[127:96];
        endcase
    end

    // fp32 product (combinational)
    logic [31:0] prod;
    hapi_fp32_mul u_mul (.a(a_sel), .b(val), .y(prod));

    // fp32 accumulate: clear seeds from +0 (golden seeds out = 0.0)
    logic [31:0] addend, sum;
    assign addend = clear ? 32'h0000_0000 : acc;
    hapi_fp32_add u_add (.a(addend), .b(prod), .y(sum));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc <= 32'h0000_0000;
        else if (en)
            acc <= sum;
    end
endmodule
