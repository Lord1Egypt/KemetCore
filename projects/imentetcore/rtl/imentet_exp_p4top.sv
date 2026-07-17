// P&R wrapper for ImentetCore exp (KemetCore Phase 4 P&R)
//
// Wraps the combinational imentet_exp datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module imentet_exp_p4top (
    input  logic        clk,
    input  logic [31:0] x,
    output logic [31:0] y
);
    logic [31:0] x_reg;
    logic [31:0] y_comb;

    always_ff @(posedge clk) begin
        x_reg <= x;
        y     <= y_comb;
    end

    imentet_exp u_core (
        .x(x_reg),
        .y(y_comb)
    );
endmodule
