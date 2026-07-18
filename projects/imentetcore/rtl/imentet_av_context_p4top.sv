// P&R wrapper for ImentetCore av_context (KemetCore Phase 4 P&R)
//
// Wraps the combinational imentet_av_context datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R. The underlying
// module has parameter L=4, DV=4 by default.

module imentet_av_context_p4top (
    input  logic                   clk,
    input  logic [32*4-1:0]        w,
    input  logic [32*4*4-1:0]      v,
    output logic [32*4-1:0]        ctx
);
    logic [32*4-1:0]   w_reg;
    logic [32*4*4-1:0] v_reg;
    logic [32*4-1:0]   ctx_comb;

    always_ff @(posedge clk) begin
        w_reg <= w;
        v_reg <= v;
        ctx   <= ctx_comb;
    end

    imentet_av_context #(
        .L(4),
        .DV(4)
    ) u_core (
        .w(w_reg),
        .v(v_reg),
        .ctx(ctx_comb)
    );
endmodule
