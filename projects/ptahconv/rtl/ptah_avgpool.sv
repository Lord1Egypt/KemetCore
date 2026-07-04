// PtahConv — fp32 2x2 average-pooling — KemetCore Phase 2 RTL
//
// Mean of a 2x2 window of four fp32 lanes in the fixed datapath order:
//   s = ((a + b) + c) + d     (three correctly-rounded fp32 adds, hapi_fp32_add)
//   y = s * 0.25              (exact multiply by 2^-2, hapi_fp32_mul)
// Purely combinational. Bit-exact vs golden ptah_conv.avgpool2x2.

module ptah_avgpool (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    input  logic [31:0] d,
    output logic [31:0] y
);
    wire [31:0] s0, s1, s2;
    hapi_fp32_add u_ab  (.a(a),  .b(b), .y(s0));
    hapi_fp32_add u_abc (.a(s0), .b(c), .y(s1));
    hapi_fp32_add u_sum (.a(s1), .b(d), .y(s2));
    // 32'h3E800000 == fp32 0.25
    hapi_fp32_mul u_q   (.a(s2), .b(32'h3E80_0000), .y(y));
endmodule
