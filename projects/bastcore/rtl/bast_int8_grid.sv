// BastCore — R x C output-stationary systolic INT8 MAC grid (KemetCore Phase 2 RTL)
//
// The integer (quantized) sibling of bast_mac_grid: a tile of bast_int8_mac PEs
// wired as an output-stationary systolic array. Signed INT8 operands flow EAST (a)
// and SOUTH (b), one neighbour hop per cycle, while each PE keeps its own INT32
// accumulator stationary, so the tile ABUTS (replicate the generate to grow it).
//
// Dataflow: with a registered hop per row/column, PE(i,j) at cycle t sees a_in[i]
// from cycle (t-j) and b_in[j] from (t-i). Feeding row i skewed by i and column j
// skewed by j (zero-padded outside the K window) makes PE(i,j) accumulate
// A[i][k]*B[k][j] over k=0..K-1. INT32 addition is associative and the zero pads
// add 0, so the result equals the golden int8 matmul exactly (no ordering caveat,
// unlike the fp32 grid).
//
// Each PE reuses the cocotb-verified bast_int8_mac. Bit-exact vs golden.int8_matmul
// — see tb/test_int8_grid.py.

module bast_int8_grid #(
    parameter int R = 4,
    parameter int C = 4
) (
    input  logic           clk,
    input  logic           rst_n,
    input  logic           clear,        // per-PE fast-zero (tb uses rst_n flush)
    input  logic           en,           // advance the array
    input  logic [8*R-1:0] a_in,         // west edge: row i int8 = a_in[8*i +: 8]
    input  logic [8*C-1:0] b_in,         // north edge: col j int8 = b_in[8*j +: 8]
    input  logic [7:0]     rd_row,
    input  logic [7:0]     rd_col,
    output logic [31:0]    out_acc       // acc[rd_row][rd_col] (combinational)
);
    logic [7:0]  aw   [0:R-1][0:C-1];
    logic [7:0]  bn   [0:R-1][0:C-1];
    logic [7:0]  areg [0:R-1][0:C-1];
    logic [7:0]  breg [0:R-1][0:C-1];
    logic [31:0] acc  [0:R-1][0:C-1];

    genvar gi, gj;
    generate
        for (gi = 0; gi < R; gi = gi + 1) begin : row
            for (gj = 0; gj < C; gj = gj + 1) begin : col
                if (gj == 0) assign aw[gi][gj] = a_in[8*gi +: 8];
                else         assign aw[gi][gj] = areg[gi][gj-1];
                if (gi == 0) assign bn[gi][gj] = b_in[8*gj +: 8];
                else         assign bn[gi][gj] = breg[gi-1][gj];

                bast_int8_mac u_pe (
                    .clk(clk), .rst_n(rst_n), .en(en), .clear(clear),
                    .a(aw[gi][gj]), .b(bn[gi][gj]), .acc(acc[gi][gj])
                );

                always_ff @(posedge clk or negedge rst_n) begin
                    if (!rst_n) begin
                        areg[gi][gj] <= 8'h00;
                        breg[gi][gj] <= 8'h00;
                    end else if (en) begin
                        areg[gi][gj] <= aw[gi][gj];
                        breg[gi][gj] <= bn[gi][gj];
                    end
                end
            end
        end
    endgenerate

    localparam int RW = (R > 1) ? $clog2(R) : 1;
    localparam int CW = (C > 1) ? $clog2(C) : 1;
    assign out_acc = acc[rd_row[RW-1:0]][rd_col[CW-1:0]];
endmodule
