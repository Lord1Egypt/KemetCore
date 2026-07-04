// SobekCore — fp32 specular reflection r = d - 2*(d.n)*n — KemetCore Phase 2 RTL
//
// Reflect incident vector d about a (unit) normal n — the secondary-ray bounce
// primitive. Purely combinational, in the fixed datapath order:
//   k     = dot3(d, n)          -- fp32 dot product          (sobek_dot3)
//   two_k = 2 * k               -- fp32 multiply by 2.0       (hapi_fp32_mul)
//   s_i   = two_k * n_i         -- fp32 scale                 (hapi_fp32_mul)
//   r_i   = d_i - s_i           -- fp32 subtract, d + (-s)    (hapi_fp32_add)
// fp32 negation is exact, so a - b is realised by flipping the subtrahend sign
// bit before the add. Bit-exact vs the fp32 golden sobek_fp32.reflect — see
// tb/test_reflect.py.

module sobek_reflect (
    input  logic [31:0] d0, d1, d2,
    input  logic [31:0] n0, n1, n2,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] k, two_k;
    logic [31:0] s0, s1, s2;

    // k = dot3(d, n)
    sobek_dot3 u_dot (.a0(d0), .a1(d1), .a2(d2),
                      .b0(n0), .b1(n1), .b2(n2), .y(k));

    // two_k = 2.0 * k   (32'h40000000 == fp32 2.0)
    hapi_fp32_mul u_two (.a(32'h4000_0000), .b(k), .y(two_k));

    // s_i = two_k * n_i
    hapi_fp32_mul u_s0 (.a(two_k), .b(n0), .y(s0));
    hapi_fp32_mul u_s1 (.a(two_k), .b(n1), .y(s1));
    hapi_fp32_mul u_s2 (.a(two_k), .b(n2), .y(s2));

    // r_i = d_i - s_i = d_i + (-s_i)
    hapi_fp32_add u_r0 (.a(d0), .b({~s0[31], s0[30:0]}), .y(r0));
    hapi_fp32_add u_r1 (.a(d1), .b({~s1[31], s1[30:0]}), .y(r1));
    hapi_fp32_add u_r2 (.a(d2), .b({~s2[31], s2[30:0]}), .y(r2));
endmodule
