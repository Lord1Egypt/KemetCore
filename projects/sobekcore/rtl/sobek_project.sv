// SobekCore — fp32 vector projection proj_b(a) = (a.b / b.b) * b — Phase 2 RTL
//
// The component of a along b. Purely combinational, fixed datapath order:
//   ab = dot3(a, b)     -- fp32 dot product        (sobek_dot3)
//   bb = dot3(b, b)     -- fp32 sum of squares of b (sobek_dot3)
//   s  = ab / bb        -- correctly-rounded divide (hapi_fp32_div)
//   c_i = s * b_i       -- fp32 scale               (hapi_fp32_mul)
// Bit-exact vs the fp32 golden sobek_fp32.project — see tb/test_project.py.

module sobek_project (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] c0, c1, c2
);
    logic [31:0] ab, bb, s;

    sobek_dot3 u_ab (.a0(a0), .a1(a1), .a2(a2), .b0(b0), .b1(b1), .b2(b2), .y(ab));
    sobek_dot3 u_bb (.a0(b0), .a1(b1), .a2(b2), .b0(b0), .b1(b1), .b2(b2), .y(bb));

    hapi_fp32_div u_div (.a(ab), .b(bb), .y(s));

    hapi_fp32_mul u_c0 (.a(s), .b(b0), .y(c0));
    hapi_fp32_mul u_c1 (.a(s), .b(b1), .y(c1));
    hapi_fp32_mul u_c2 (.a(s), .b(b2), .y(c2));
endmodule
