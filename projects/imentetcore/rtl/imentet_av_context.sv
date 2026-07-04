// ImentetCore — fp32 weighted value accumulation (context = P·V) — Phase 2 RTL
//
// The second half of attention: given L attention weights w and an L×DV value
// matrix V, produce the DV-wide context vector
//   context[k] = sum_j w[j] * V[j][k]
// Each output element is an independent fixed left-to-right fp32 MAC (products
// into an adder chain), matching golden imentet_fp32.av_context bit-for-bit. The
// weights come from softmax (float64 math model); given them, this is bit-exact.
// Built from the correctly-rounded HapiCore fp32 primitives. Purely combinational.
// Bit-exact vs the fp32 golden — see tb/test_av_context.py.

module imentet_av_context #(
    parameter int L  = 4,
    parameter int DV = 4
) (
    input  logic [32*L-1:0]     w,    // L fp32 weights, w[j] = w[32*j +: 32]
    input  logic [32*L*DV-1:0]  v,    // L*DV fp32 values, row-major V[j][k] at 32*(j*DV+k)
    output logic [32*DV-1:0]    ctx   // DV fp32 context, ctx[k] = ctx[32*k +: 32]
);
    genvar k, j;
    generate
        for (k = 0; k < DV; k++) begin : g_out
            // products p_j = w[j] * V[j][k]
            logic [31:0] p [L];
            for (j = 0; j < L; j++) begin : g_mul
                hapi_fp32_mul u_mul (.a(w[32*j +: 32]),
                                     .b(v[32*(j*DV + k) +: 32]),
                                     .y(p[j]));
            end
            // left-to-right accumulation chain
            logic [31:0] acc [L];
            assign acc[0] = p[0];
            for (j = 1; j < L; j++) begin : g_add
                hapi_fp32_add u_add (.a(acc[j-1]), .b(p[j]), .y(acc[j]));
            end
            assign ctx[32*k +: 32] = acc[L-1];
        end
    endgenerate
endmodule
