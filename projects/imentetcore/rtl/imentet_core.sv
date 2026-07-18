// ImentetCore — integrated flash attention datapath — KemetCore Phase 2 RTL
//
// Top-level combinational datapath for scaled dot-product attention:
//   context = softmax(Q * K^T * scale + mask) * V
// 
// Instantiates the full pipeline for a single Query vector against LS Keys/Values:
// 1. LS instances of imentet_qk_score (Q * K^T * scale)
// 2. 1 instance of imentet_mask_add (+ mask)
// 3. 1 instance of imentet_rowmax_sub (max stabilization)
// 4. LS instances of imentet_exp (exp)
// 5. 1 instance of imentet_softmax_norm (normalization)
// 6. 1 instance of imentet_av_context (* V)
//
// Verified vs golden imentet_attention.attention() in tb/test_core.py.

module imentet_core #(
    parameter int D  = 8,
    parameter int LS = 8,
    parameter int DV = 8
) (
    input  logic [32*D-1:0]     q,     // 1 fp32 query vector
    input  logic [32*LS*D-1:0]  k,     // LS fp32 key vectors, k[j] at 32*(j*D)
    input  logic [32*LS*DV-1:0] v,     // LS fp32 value vectors, v[j] at 32*(j*DV)
    input  logic [31:0]         s,     // fp32 scale (1/sqrt(d))
    input  logic [32*LS-1:0]    m,     // LS fp32 mask terms (0 or -inf)
    output logic [32*DV-1:0]    ctx    // 1 fp32 context vector
);

    // 1. QK Score
    logic [32*LS-1:0] raw_scores;
    genvar j;
    generate
        for (j = 0; j < LS; j++) begin : g_qk
            imentet_qk_score #(.D(D)) u_qk (
                .q(q),
                .k(k[32*(j*D) +: 32*D]),
                .s(s),
                .score(raw_scores[32*j +: 32])
            );
        end
    endgenerate

    // 2. Mask Add
    logic [32*LS-1:0] masked_scores;
    imentet_mask_add #(.LS(LS)) u_mask (
        .x(raw_scores),
        .m(m),
        .y(masked_scores)
    );

    // 3. Rowmax Sub
    logic [32*LS-1:0] stable_scores;
    imentet_rowmax_sub #(.LS(LS)) u_rowmax (
        .x(masked_scores),
        .y(stable_scores)
    );

    // 4. Exp
    logic [32*LS-1:0] exp_vals;
    generate
        for (j = 0; j < LS; j++) begin : g_exp
            imentet_exp u_exp (
                .x(stable_scores[32*j +: 32]),
                .y(exp_vals[32*j +: 32])
            );
        end
    endgenerate

    // 5. Softmax Norm
    logic [32*LS-1:0] probs;
    imentet_softmax_norm #(.LS(LS)) u_norm (
        .e(exp_vals),
        .p(probs)
    );

    // 6. AV Context
    imentet_av_context #(.L(LS), .DV(DV)) u_av (
        .w(probs),
        .v(v),
        .ctx(ctx)
    );

endmodule
