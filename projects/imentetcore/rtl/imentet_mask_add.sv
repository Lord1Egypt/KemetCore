// ImentetCore — additive attention mask y = x + m — KemetCore Phase 2 RTL
//
// Apply a causal / padding mask to a length-LS score row before softmax:
//   y_j = x_j + m_j    -- fp32 add (hapi_fp32_add)
// The mask is 0.0 for visible positions and -inf for masked ones, so a masked
// score becomes -inf and contributes exp(-inf)=0. Purely combinational, LS
// parallel correctly-rounded fp32 adds. Bit-exact vs golden imentet_fp32.mask_add.

module imentet_mask_add #(
    parameter int LS = 8
) (
    input  logic [32*LS-1:0] x,   // LS fp32 scores
    input  logic [32*LS-1:0] m,   // LS fp32 mask terms (0 or -inf)
    output logic [32*LS-1:0] y    // LS fp32 masked scores
);
    genvar i;
    generate
        for (i = 0; i < LS; i++) begin : g_add
            hapi_fp32_add u_add (.a(x[32*i +: 32]), .b(m[32*i +: 32]), .y(y[32*i +: 32]));
        end
    endgenerate
endmodule
