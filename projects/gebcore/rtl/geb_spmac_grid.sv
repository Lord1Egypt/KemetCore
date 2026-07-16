// GebCore — R x C output-stationary sparse systolic grid (KemetCore Phase 2 RTL)
//
// A tile of geb_spmac processing elements wired as an output-stationary
// systolic array: activations (groups of 4 fp32s, 128-bit) flow EAST, and
// sparse weights (val 32-bit fp32, idx 2-bit) flow SOUTH, one hop per cycle,
// while each PE keeps its fp32 accumulator stationary.
//
// This is exactly the PtahCore tile-abutment methodology applied to GebCore's
// 2:4 sparse MAC. Because 2:4 sparsity keeps 2 weights per group of 4, the
// controller feeds each 128-bit activation group for 2 consecutive cycles,
// paired with the 2 kept weights from the compressed matrix.
//
// Dataflow is skewed: PE(i,j) at cycle t receives row i's A-stream skewed by i
// cycles, and column j's sparse weight stream skewed by j cycles, accumulating
// exactly in the golden's k-order.
//
// Bit-exact vs golden.sparse_matmul — see tb/test_spmac_grid.py.

module geb_spmac_grid #(
    parameter int R = 4,                 // rows  (M output dimension)
    parameter int C = 4                  // cols  (N output dimension)
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             clear,       // zero all accumulators + pipeline (pulse)
    input  logic             en,          // advance the array (accumulate + propagate)
    input  logic [128*R-1:0] a_group_in,  // west edge: row i a_group = a_group_in[128*i +: 128]
    input  logic [32*C-1:0]  val_in,      // north edge: col j val = val_in[32*j +: 32]
    input  logic [2*C-1:0]   idx_in,      // north edge: col j idx = idx_in[2*j +: 2]
    input  logic [7:0]       rd_row,      // result row to read (0..R-1)
    input  logic [7:0]       rd_col,      // result col to read (0..C-1)
    output logic [31:0]      out_acc      // acc[rd_row][rd_col] (combinational)
);
    // combinational inputs to PEs
    logic [127:0] aw  [0:R-1][0:C-1];
    logic [31:0]  vw  [0:R-1][0:C-1];
    logic [1:0]   iw  [0:R-1][0:C-1];

    // registered outputs feeding next hop
    logic [127:0] areg [0:R-1][0:C-1];
    logic [31:0]  vreg [0:R-1][0:C-1];
    logic [1:0]   ireg [0:R-1][0:C-1];

    logic [31:0]  acc  [0:R-1][0:C-1];

    genvar gi, gj;
    generate
        for (gi = 0; gi < R; gi = gi + 1) begin : row
            for (gj = 0; gj < C; gj = gj + 1) begin : col
                // west input: external A-stream at col 0, else left neighbour
                if (gj == 0) assign aw[gi][gj] = a_group_in[128*gi +: 128];
                else         assign aw[gi][gj] = areg[gi][gj-1];

                // north input: external weight stream at row 0, else upper neighbour
                if (gi == 0) begin
                    assign vw[gi][gj] = val_in[32*gj +: 32];
                    assign iw[gi][gj] = idx_in[2*gj +: 2];
                end else begin
                    assign vw[gi][gj] = vreg[gi-1][gj];
                    assign iw[gi][gj] = ireg[gi-1][gj];
                end

                // compute PE: proven geb_spmac
                geb_spmac u_pe (
                    .clk(clk), .rst_n(rst_n), .en(en), .clear(clear),
                    .a_group(aw[gi][gj]), .idx(iw[gi][gj]), .val(vw[gi][gj]),
                    .acc(acc[gi][gj])
                );

                // systolic propagation
                always_ff @(posedge clk or negedge rst_n) begin
                    if (!rst_n) begin
                        areg[gi][gj] <= 128'h0;
                        vreg[gi][gj] <= 32'h0;
                        ireg[gi][gj] <= 2'h0;
                    end else if (clear) begin
                        areg[gi][gj] <= 128'h0;
                        vreg[gi][gj] <= 32'h0;
                        ireg[gi][gj] <= 2'h0;
                    end else if (en) begin
                        areg[gi][gj] <= aw[gi][gj];
                        vreg[gi][gj] <= vw[gi][gj];
                        ireg[gi][gj] <= iw[gi][gj];
                    end
                end
            end
        end
    endgenerate

    // combinational read multiplexer
    localparam int RW = (R > 1) ? $clog2(R) : 1;
    localparam int CW = (C > 1) ? $clog2(C) : 1;
    assign out_acc = acc[rd_row[RW-1:0]][rd_col[CW-1:0]];

endmodule
