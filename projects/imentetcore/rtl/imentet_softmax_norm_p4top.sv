// P&R wrapper for ImentetCore softmax_norm (KemetCore Phase 4 P&R)
//
// Wraps the combinational imentet_softmax_norm datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R. The underlying
// module has parameter LS=8 by default.

module imentet_softmax_norm_p4top (
    input  logic             clk,
    input  logic [32*8-1:0]  e,
    output logic [32*8-1:0]  p
);
    logic [32*8-1:0] e_reg;
    logic [32*8-1:0] p_comb;

    always_ff @(posedge clk) begin
        e_reg <= e;
        p     <= p_comb;
    end

    imentet_softmax_norm #(
        .LS(8)
    ) u_core (
        .e(e_reg),
        .p(p_comb)
    );
endmodule
