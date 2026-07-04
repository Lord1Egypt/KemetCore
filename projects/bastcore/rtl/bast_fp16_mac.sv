// BastCore — fp16 multiply / fp32 accumulate MAC cell (KemetCore Phase 2 RTL)
//
// An fp16-precision processing element for the tensor core (companion to the bf16
// bast_mac and the int8 bast_int8_mac). Each cycle it multiplies an fp16 pair to
// an fp16 product, widens it EXACTLY to fp32 (fp16->fp32 is lossless — every half
// is representable in single), and accumulates into a registered fp32 sum:
//     out = sum_k fp16_widen(round_fp16(a_k * b_k))    accumulated in fp32
// (golden bast_matmul.fp16_dot). Composes the verified HapiCore primitives
// hapi_fp16_mul + hapi_fp16_to_fp32 + hapi_fp32_add.
//
// Drive a length-K dot product by pulsing `clear` with the first element and `en`
// for all K elements; `acc` holds the fp32 result one cycle after the last input.
// Bit-exact against golden.fp16_dot — see tb/test_fp16.py.

module bast_fp16_mac (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        en,      // accumulate the (a,b) product this cycle
    input  logic        clear,   // start a fresh dot product (ignore old acc)
    input  logic [15:0] a,       // fp16
    input  logic [15:0] b,       // fp16
    output logic [31:0] acc      // fp32 running accumulator (registered)
);
    // fp16 product (combinational)
    logic [15:0] prod_fp16;
    hapi_fp16_mul u_mul (.a(a), .b(b), .y(prod_fp16));

    // fp16 -> fp32 exact widening
    logic [31:0] prod_fp32;
    hapi_fp16_to_fp32 u_widen (.a(prod_fp16), .y(prod_fp32));

    // fp32 accumulate: clear starts from +0 (golden seeds acc = 0.0)
    logic [31:0] addend, sum;
    assign addend = clear ? 32'h0000_0000 : acc;
    hapi_fp32_add u_add (.a(addend), .b(prod_fp32), .y(sum));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc <= 32'h0000_0000;
        else if (en)
            acc <= sum;
    end
endmodule
