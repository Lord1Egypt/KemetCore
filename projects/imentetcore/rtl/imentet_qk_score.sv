// ImentetCore — fp32 scaled dot-product attention score — KemetCore Phase 2 RTL
//
// One attention score for a (query, key) pair over a D=8 head sub-tile:
//   raw   = sum_i q_i * k_i          (fixed left-to-right fp32 MAC)
//   score = raw * s                  (s = 1/sqrt(d) scale, fp32 multiply)
// Purely combinational, built from the correctly-rounded HapiCore fp32 primitives.
// The eight products feed a left-to-right adder chain ((((p0+p1)+p2)+...)+p7) so
// the rounding order matches the golden imentet_fp32.dot exactly. This is the
// bit-exact part of attention; the softmax (exp) stays in the float64 math model.
// Bit-exact vs the fp32 golden imentet_fp32.score — see tb/test_qk_score.py.

module imentet_qk_score #(
    parameter int D = 8
) (
    input  logic [32*D-1:0] q,     // D fp32 query elements, element i = q[32*i +: 32]
    input  logic [32*D-1:0] k,     // D fp32 key elements
    input  logic [31:0]     s,     // fp32 scale (1/sqrt(d))
    output logic [31:0]     score  // fp32 scaled dot-product score
);
    // per-lane products p_i = q_i * k_i
    logic [31:0] p [D];
    genvar i;
    generate
        for (i = 0; i < D; i++) begin : g_mul
            hapi_fp32_mul u_mul (.a(q[32*i +: 32]), .b(k[32*i +: 32]), .y(p[i]));
        end
    endgenerate

    // left-to-right accumulation chain: acc_0 = p0; acc_j = acc_{j-1} + p_j
    logic [31:0] acc [D];
    assign acc[0] = p[0];
    generate
        for (i = 1; i < D; i++) begin : g_add
            hapi_fp32_add u_add (.a(acc[i-1]), .b(p[i]), .y(acc[i]));
        end
    endgenerate

    // score = raw * s
    hapi_fp32_mul u_scale (.a(acc[D-1]), .b(s), .y(score));
endmodule
