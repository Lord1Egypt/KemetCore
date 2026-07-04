// SobekCore — fp32 vector rejection r = a - proj_b(a) — KemetCore Phase 2 RTL
//
// The component of a perpendicular to b (a = proj_b(a) + reject_b(a)). Purely
// combinational, fixed datapath order:
//   p_i = proj_b(a)_i     -- parallel component (sobek_project)
//   r_i = a_i - p_i       -- fp32 subtract, a + (-p) exact negation (hapi_fp32_add)
// Bit-exact vs the fp32 golden sobek_fp32.reject — see tb/test_reject.py.

module sobek_reject (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] p0, p1, p2;

    // parallel component p = proj_b(a)
    sobek_project u_proj (.a0(a0), .a1(a1), .a2(a2), .b0(b0), .b1(b1), .b2(b2),
                          .c0(p0), .c1(p1), .c2(p2));

    // r_i = a_i - p_i = a_i + (-p_i)
    hapi_fp32_add u_r0 (.a(a0), .b({~p0[31], p0[30:0]}), .y(r0));
    hapi_fp32_add u_r1 (.a(a1), .b({~p1[31], p1[30:0]}), .y(r1));
    hapi_fp32_add u_r2 (.a(a2), .b({~p2[31], p2[30:0]}), .y(r2));
endmodule
