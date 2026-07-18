// P&R wrapper for ImentetCore rowmax_sub (KemetCore Phase 4 P&R)
//
// Wraps the combinational imentet_rowmax_sub datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R. The underlying
// module has parameter LS=8 by default.

module imentet_rowmax_sub_p4top (
    input  logic             clk,
    input  logic [32*8-1:0]  x,
    output logic [32*8-1:0]  y
);
    logic [32*8-1:0] x_reg;
    logic [32*8-1:0] y_comb;

    always_ff @(posedge clk) begin
        x_reg <= x;
        y     <= y_comb;
    end

    imentet_rowmax_sub #(
        .LS(8)
    ) u_core (
        .x(x_reg),
        .y(y_comb)
    );
endmodule
