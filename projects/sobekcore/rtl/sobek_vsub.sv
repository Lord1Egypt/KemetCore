// SobekCore — fp32 3-vector subtract — KemetCore Phase 2 RTL
//
// Builds the Moller-Trumbore edge vectors: e1 = v1 - v0, e2 = v2 - v0,
// tvec = origin - v0. Purely combinational, three independent fp32 subtracts,
// each realised as a + (-b): fp32 negation is exact, so the subtrahend's sign
// bit is flipped before hapi_fp32_add. Bit-exact vs the fp32 golden
// sobek_fp32.vsub — see tb/test_vsub.py.

module sobek_vsub (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] d0, d1, d2
);
    hapi_fp32_add u_s0 (.a(a0), .b({~b0[31], b0[30:0]}), .y(d0));
    hapi_fp32_add u_s1 (.a(a1), .b({~b1[31], b1[30:0]}), .y(d1));
    hapi_fp32_add u_s2 (.a(a2), .b({~b2[31], b2[30:0]}), .y(d2));
endmodule
