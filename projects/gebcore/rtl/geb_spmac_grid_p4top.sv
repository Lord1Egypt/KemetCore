// P&R wrapper for GebCore geb_spmac_grid (KemetCore Phase 4 P&R)
//
// Wraps the 4x4 sparse systolic array in registers to ensure exact timing
// constraint boundaries during ASAP7 synthesis and P&R.

module geb_spmac_grid_p4top (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             clear,
    input  logic             en,
    input  logic [128*4-1:0] a_group_in,
    input  logic [32*4-1:0]  val_in,
    input  logic [2*4-1:0]   idx_in,
    input  logic [7:0]       rd_row,
    input  logic [7:0]       rd_col,
    output logic [31:0]      out_acc
);
    logic             clear_reg;
    logic             en_reg;
    logic [128*4-1:0] a_group_in_reg;
    logic [32*4-1:0]  val_in_reg;
    logic [2*4-1:0]   idx_in_reg;
    logic [7:0]       rd_row_reg;
    logic [7:0]       rd_col_reg;
    logic [31:0]      out_acc_comb;

    always_ff @(posedge clk) begin
        clear_reg      <= clear;
        en_reg         <= en;
        a_group_in_reg <= a_group_in;
        val_in_reg     <= val_in;
        idx_in_reg     <= idx_in;
        rd_row_reg     <= rd_row;
        rd_col_reg     <= rd_col;
        out_acc        <= out_acc_comb;
    end

    geb_spmac_grid #(
        .R(4),
        .C(4)
    ) u_core (
        .clk(clk),
        .rst_n(rst_n),
        .clear(clear_reg),
        .en(en_reg),
        .a_group_in(a_group_in_reg),
        .val_in(val_in_reg),
        .idx_in(idx_in_reg),
        .rd_row(rd_row_reg),
        .rd_col(rd_col_reg),
        .out_acc(out_acc_comb)
    );
endmodule
