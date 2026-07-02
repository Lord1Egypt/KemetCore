// SobekCore — fp32 3-element dot product — KemetCore Phase 2 RTL
//
// The workhorse primitive of the Moller-Trumbore ray-triangle intersector: every
// det / u / v / t term is a 3-vector dot product. Purely combinational, built from
// the correctly-rounded HapiCore fp32 primitives:
//   p_i = a_i * b_i            (hapi_fp32_mul, round-to-nearest-even)
//   y   = (p0 + p1) + p2       (hapi_fp32_add, left-to-right, RNE)
// The evaluation order is fixed so the result is bit-exact vs the fp32 golden
// sobek_fp32.dot3 — see tb/test_dot3.py.

module sobek_dot3 (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] y
);
    logic [31:0] p0, p1, p2;
    logic [31:0] s01;

    hapi_fp32_mul u_m0 (.a(a0), .b(b0), .y(p0));
    hapi_fp32_mul u_m1 (.a(a1), .b(b1), .y(p1));
    hapi_fp32_mul u_m2 (.a(a2), .b(b2), .y(p2));

    hapi_fp32_add u_a0 (.a(p0),  .b(p1), .y(s01));  // p0 + p1
    hapi_fp32_add u_a1 (.a(s01), .b(p2), .y(y));    // (p0+p1) + p2
endmodule
