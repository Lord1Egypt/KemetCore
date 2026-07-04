// SobekCore — fp32 vector normalize v / ||v|| — KemetCore Phase 2 RTL
//
// Ray-direction conditioning: reduce a 3-vector to unit length. Purely
// combinational, assembled from verified SobekCore / HapiCore fp32 primitives in
// the fixed datapath order:
//   d   = dot3(v, v)      -- sum of squares (sobek_dot3: 3 fp32 muls + 2 adds)
//   len = sqrt(d)         -- correctly-rounded fp32 sqrt  (hapi_fp32_sqrt)
//   inv = 1 / len         -- correctly-rounded fp32 recip (hapi_fp32_div 1.0 / len)
//   c_i = inv * v_i       -- fp32 scale                   (hapi_fp32_mul)
// Bit-exact vs the fp32 golden sobek_fp32.normalize — see tb/test_normalize.py.

module sobek_normalize (
    input  logic [31:0] v0, v1, v2,
    output logic [31:0] c0, c1, c2
);
    logic [31:0] d, len, inv;

    // d = dot3(v, v)
    sobek_dot3 u_dot (.a0(v0), .a1(v1), .a2(v2),
                      .b0(v0), .b1(v1), .b2(v2), .y(d));

    // len = sqrt(d)
    hapi_fp32_sqrt u_sqrt (.x(d), .y(len));

    // inv = 1.0 / len   (32'h3F800000 == fp32 1.0)
    hapi_fp32_div u_div (.a(32'h3F80_0000), .b(len), .y(inv));

    // c_i = inv * v_i
    hapi_fp32_mul u_m0 (.a(inv), .b(v0), .y(c0));
    hapi_fp32_mul u_m1 (.a(inv), .b(v1), .y(c1));
    hapi_fp32_mul u_m2 (.a(inv), .b(v2), .y(c2));
endmodule
