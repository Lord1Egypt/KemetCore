// ImentetCore — softmax normalization p = e / sum(e) — KemetCore Phase 2 RTL
//
// The divide half of softmax: turn a length-LS vector of already-exp'd weights
// into probabilities. Purely combinational, fixed datapath order:
//   s   = ((e_0 + e_1) + …) + e_{LS-1}   -- fp32 fixed-order sum (adder chain)
//   inv = 1 / s                          -- correctly-rounded fp32 recip (hapi_fp32_div)
//   p_j = e_j * inv                      -- fp32 scale (hapi_fp32_mul)
// The exp() itself stays in the float64 math model; given the exp'd inputs this
// normalisation is bit-exact vs golden imentet_fp32.softmax_norm — see tb.

module imentet_softmax_norm #(
    parameter int LS = 8
) (
    input  logic [32*LS-1:0] e,   // LS fp32 exp'd weights, e_i = e[32*i +: 32]
    output logic [32*LS-1:0] p    // LS fp32 probabilities, p_i = e_i / sum
);
    // left-to-right sum chain
    logic [31:0] acc [LS];
    assign acc[0] = e[31:0];
    genvar i;
    generate
        for (i = 1; i < LS; i++) begin : g_sum
            hapi_fp32_add u_add (.a(acc[i-1]), .b(e[32*i +: 32]), .y(acc[i]));
        end
    endgenerate

    // inv = 1.0 / sum   (32'h3F800000 == fp32 1.0)
    logic [31:0] inv;
    hapi_fp32_div u_div (.a(32'h3F80_0000), .b(acc[LS-1]), .y(inv));

    // p_j = e_j * inv
    generate
        for (i = 0; i < LS; i++) begin : g_scale
            hapi_fp32_mul u_mul (.a(e[32*i +: 32]), .b(inv), .y(p[32*i +: 32]));
        end
    endgenerate
endmodule
