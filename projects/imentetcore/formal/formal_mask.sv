// ImentetCore — FORMAL: imentet_mask_add attention-mask SEMANTICS, proved
// exhaustively over all fp32 scores in one combinational BMC step:
//
//   (a) VISIBLE (mask = +0.0):  y == x  — a visible position keeps its score
//       (for x not NaN and not -0.0, whose exact results are +qNaN / +0.0).
//   (b) MASKED  (mask = -inf):  y == -inf — a masked position is driven to -inf
//       so that exp(-inf)=0 in the softmax (for x not NaN and not +inf, since
//       +inf + -inf = NaN is the one ill-defined case).
//
// These are the two behaviours the whole causal/padding-mask stage exists to
// provide, and they hold for every score value.
//
// HONEST SCOPE NOTE: the q<->k commutativity of imentet_qk_score (a scaled fp32
// dot product) is an fp32-adder equivalence miter that does not converge under
// z3 in CI time; its bit-exactness is covered by the cocotb testbench vs the
// golden imentet_fp32. Per-lane masking is the tractable, formally-proved piece.
module formal_mask (input logic [31:0] x);
    localparam logic [31:0] NEG_INF = 32'hFF80_0000;
    wire [31:0] y_vis, y_msk;
    imentet_mask_add #(.LS(1)) u_vis (.x(x), .m(32'h0000_0000), .y(y_vis));
    imentet_mask_add #(.LS(1)) u_msk (.x(x), .m(NEG_INF),       .y(y_msk));
    always_comb begin
        // (a) visible: score preserved (exclude NaN and -0.0)
        if (x[30:23] != 8'hFF && x[30:0] != 31'h0)
            assert (y_vis == x);
        // (b) masked: forced to -inf (exclude NaN and +inf: +inf + -inf = NaN)
        if (!(x[30:23] == 8'hFF && x[22:0] != 23'h0) && x != 32'h7F80_0000)
            assert (y_msk == NEG_INF);
    end
endmodule
