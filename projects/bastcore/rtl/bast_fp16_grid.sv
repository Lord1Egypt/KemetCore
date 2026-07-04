// BastCore — R x C output-stationary systolic fp16 MAC grid (KemetCore Phase 2 RTL)
//
// A tile of bast_mac processing elements wired as a classic output-stationary
// systolic array: fp16 operands flow EAST (a, west->east) and SOUTH (b,
// north->south), one neighbour hop per cycle, while each PE keeps its own fp32
// accumulator stationary. Because every PE only ever talks to its immediate
// neighbours, the tile ABUTS — replicate the generate to grow the array (the
// PtahCore tile-abutment methodology); the synthesized instance here is the
// default 4x4, the 16x16 (256-PE) array is the same module with R=C=16. Identical dataflow to bast_mac_grid; only the PE precision (fp16) differs.
//
// Each PE reuses the cocotb-verified `bast_fp16_mac` (hapi_fp16_mul + exact fp16->fp32
// widen + registered hapi_fp32_add) for its compute, so the datapath is already
// proven; this module only adds the a/b propagation registers and edge wiring.
//
// Dataflow / bit-exactness: with a registered hop per column/row, PE(i,j) at
// cycle t multiplies a_in[i] presented at cycle (t-j) by b_in[j] presented at
// (t-i). Feeding row i's A-stream skewed by i cycles and column j's B-stream
// skewed by j cycles (zero-padded outside the K-long window) makes PE(i,j) see
// A[i][k]*B[k][j] on CONSECUTIVE cycles k=0..K-1, so it accumulates in exactly the
// golden's k-order. The zero-padding is a true no-op (x + (+/-0) == x in fp32),
// so the result equals sum_k round_fp16(A[i][k]*B[k][j]) bit-for-bit.
//   * rst_n : flush all accumulators + propagation registers to zero before a matmul.
//   * en    : stream the skewed, zero-padded operands; hold high until drained.
//             accumulation runs from zero (each PE adds 0+prod on its first product).
//   * clear : per-PE bast_mac fast-zero (acc<=0+prod when pulsed with en); the tb
//             uses the rst_n flush instead, so it is held low here.
//   * read  : out_acc = acc[rd_row][rd_col] combinationally once drained.
//
// Bit-exact vs golden.matmul across shapes/sizes — see tb/test_mac_grid.py.
// Yosys-portable: generate-instantiated PEs, register-array propagation.

module bast_fp16_grid #(
    parameter int R = 4,                 // rows  (M output dimension)
    parameter int C = 4                  // cols  (N output dimension)
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            clear,       // zero all accumulators + pipeline (pulse)
    input  logic            en,          // advance the array (accumulate + propagate)
    input  logic [16*R-1:0] a_in,        // west edge: row i bf16 = a_in[16*i +: 16]
    input  logic [16*C-1:0] b_in,        // north edge: col j bf16 = b_in[16*j +: 16]
    input  logic [7:0]      rd_row,      // result row to read (0..R-1)
    input  logic [7:0]      rd_col,      // result col to read (0..C-1)
    output logic [31:0]     out_acc      // acc[rd_row][rd_col] (combinational)
);
    // a entering each PE from the west, b entering from the north (combinational),
    // and the per-PE registered copies that feed the east / south neighbour.
    logic [15:0] aw   [0:R-1][0:C-1];
    logic [15:0] bn   [0:R-1][0:C-1];
    logic [15:0] areg [0:R-1][0:C-1];
    logic [15:0] breg [0:R-1][0:C-1];
    logic [31:0] acc  [0:R-1][0:C-1];

    genvar gi, gj;
    generate
        for (gi = 0; gi < R; gi = gi + 1) begin : row
            for (gj = 0; gj < C; gj = gj + 1) begin : col
                // west input: external A-stream at column 0, else the left neighbour's reg
                if (gj == 0) assign aw[gi][gj] = a_in[16*gi +: 16];
                else         assign aw[gi][gj] = areg[gi][gj-1];
                // north input: external B-stream at row 0, else the upper neighbour's reg
                if (gi == 0) assign bn[gi][gj] = b_in[16*gj +: 16];
                else         assign bn[gi][gj] = breg[gi-1][gj];

                // compute PE: proven bast_fp16_mac (fp16 mul + fp32 accumulate)
                bast_fp16_mac u_pe (
                    .clk(clk), .rst_n(rst_n), .en(en), .clear(clear),
                    .a(aw[gi][gj]), .b(bn[gi][gj]), .acc(acc[gi][gj])
                );

                // systolic propagation: forward this cycle's operands one hop.
                // rst_n flushes the pipeline (and bast_mac's acc) to zero between
                // matmuls; streaming zeros also drains it naturally.
                always_ff @(posedge clk or negedge rst_n) begin
                    if (!rst_n) begin
                        areg[gi][gj] <= 16'h0000;
                        breg[gi][gj] <= 16'h0000;
                    end else if (en) begin
                        areg[gi][gj] <= aw[gi][gj];
                        breg[gi][gj] <= bn[gi][gj];
                    end
                end
            end
        end
    endgenerate

    // combinational result read (drain the array first, then address it).
    // Slice the read addresses to the array index width (Verilator width-strict).
    localparam int RW = (R > 1) ? $clog2(R) : 1;
    localparam int CW = (C > 1) ? $clog2(C) : 1;
    assign out_acc = acc[rd_row[RW-1:0]][rd_col[CW-1:0]];
endmodule
