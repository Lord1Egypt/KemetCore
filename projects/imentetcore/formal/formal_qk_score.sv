// ImentetCore — FORMAL: imentet_qk_score is symmetric in q<->k (the Q.K dot
// product commutes), for ALL query/key tiles and scale, over the whole space.
module formal_qk_score #(parameter int D = 8) (
    input logic [32*D-1:0] q, k, input logic [31:0] s
);
    wire [31:0] score_qk, score_kq;
    imentet_qk_score #(.D(D)) u_qk (.q(q), .k(k), .s(s), .score(score_qk));
    imentet_qk_score #(.D(D)) u_kq (.q(k), .k(q), .s(s), .score(score_kq));
    always_comb assert (score_qk == score_kq);
endmodule
