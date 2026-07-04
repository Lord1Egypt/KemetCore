// SobekCore — fp32 ray parametric point p = o + t*d — KemetCore Phase 2 RTL
//
// Evaluate the position at distance t along a ray (origin o, direction d) — the
// most-used ray operation, e.g. the hit point once the Moller-Trumbore t is known.
// Purely combinational, fixed datapath order:
//   s_i = t * d_i     -- fp32 scale (hapi_fp32_mul)
//   p_i = o_i + s_i   -- fp32 add   (hapi_fp32_add)
// Bit-exact vs the fp32 golden sobek_fp32.ray_point — see tb/test_raypoint.py.

module sobek_ray_point (
    input  logic [31:0] o0, o1, o2,
    input  logic [31:0] t,
    input  logic [31:0] d0, d1, d2,
    output logic [31:0] p0, p1, p2
);
    logic [31:0] s0, s1, s2;

    // s_i = t * d_i
    hapi_fp32_mul u_s0 (.a(t), .b(d0), .y(s0));
    hapi_fp32_mul u_s1 (.a(t), .b(d1), .y(s1));
    hapi_fp32_mul u_s2 (.a(t), .b(d2), .y(s2));

    // p_i = o_i + s_i
    hapi_fp32_add u_p0 (.a(o0), .b(s0), .y(p0));
    hapi_fp32_add u_p1 (.a(o1), .b(s1), .y(p1));
    hapi_fp32_add u_p2 (.a(o2), .b(s2), .y(p2));
endmodule
