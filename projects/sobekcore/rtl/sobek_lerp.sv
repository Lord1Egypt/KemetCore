// SobekCore — fp32 linear interpolation r = a + t*(b-a) — KemetCore Phase 2 RTL
//
// Blend two 3-vectors by parameter t (e.g. interpolate a shading normal or vertex
// attribute across a triangle hit). Purely combinational, fixed datapath order:
//   e_i = b_i - a_i    -- fp32 subtract, b + (-a) exact negation (hapi_fp32_add)
//   s_i = t * e_i      -- fp32 scale                             (hapi_fp32_mul)
//   r_i = a_i + s_i    -- fp32 add                               (hapi_fp32_add)
// Bit-exact vs the fp32 golden sobek_fp32.lerp — see tb/test_lerp.py.

module sobek_lerp (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    input  logic [31:0] t,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] e0, e1, e2;
    logic [31:0] s0, s1, s2;

    // e_i = b_i - a_i = b_i + (-a_i)
    hapi_fp32_add u_e0 (.a(b0), .b({~a0[31], a0[30:0]}), .y(e0));
    hapi_fp32_add u_e1 (.a(b1), .b({~a1[31], a1[30:0]}), .y(e1));
    hapi_fp32_add u_e2 (.a(b2), .b({~a2[31], a2[30:0]}), .y(e2));

    // s_i = t * e_i
    hapi_fp32_mul u_s0 (.a(t), .b(e0), .y(s0));
    hapi_fp32_mul u_s1 (.a(t), .b(e1), .y(s1));
    hapi_fp32_mul u_s2 (.a(t), .b(e2), .y(s2));

    // r_i = a_i + s_i
    hapi_fp32_add u_r0 (.a(a0), .b(s0), .y(r0));
    hapi_fp32_add u_r1 (.a(a1), .b(s1), .y(r1));
    hapi_fp32_add u_r2 (.a(a2), .b(s2), .y(r2));
endmodule
