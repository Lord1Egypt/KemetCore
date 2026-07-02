// SobekCore — fp32 3-D cross product — KemetCore Phase 2 RTL
//
// The other Moller-Trumbore primitive: pvec = dir x edge2 and qvec = tvec x edge1
// are cross products. Purely combinational, built from the correctly-rounded
// HapiCore fp32 primitives. Each component is two fp32 products and one fp32
// subtract, where a - b is realised as a + (-b): fp32 negation is exact, so the
// sign bit of the subtrahend is simply flipped before hapi_fp32_add.
//   c0 = a1*b2 - a2*b1
//   c1 = a2*b0 - a0*b2
//   c2 = a0*b1 - a1*b0
// Bit-exact vs the fp32 golden sobek_fp32.cross — see tb/test_cross.py.

module sobek_cross (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] c0, c1, c2
);
    logic [31:0] m0p, m0n, m1p, m1n, m2p, m2n;

    // c0 = a1*b2 - a2*b1
    hapi_fp32_mul u_m0p (.a(a1), .b(b2), .y(m0p));
    hapi_fp32_mul u_m0n (.a(a2), .b(b1), .y(m0n));
    hapi_fp32_add u_a0  (.a(m0p), .b({~m0n[31], m0n[30:0]}), .y(c0));

    // c1 = a2*b0 - a0*b2
    hapi_fp32_mul u_m1p (.a(a2), .b(b0), .y(m1p));
    hapi_fp32_mul u_m1n (.a(a0), .b(b2), .y(m1n));
    hapi_fp32_add u_a1  (.a(m1p), .b({~m1n[31], m1n[30:0]}), .y(c1));

    // c2 = a0*b1 - a1*b0
    hapi_fp32_mul u_m2p (.a(a0), .b(b1), .y(m2p));
    hapi_fp32_mul u_m2n (.a(a1), .b(b0), .y(m2n));
    hapi_fp32_add u_a2  (.a(m2p), .b({~m2n[31], m2n[30:0]}), .y(c2));
endmodule
