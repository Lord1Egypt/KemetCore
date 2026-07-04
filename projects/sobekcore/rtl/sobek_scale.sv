// SobekCore — fp32 scalar-vector product — KemetCore Phase 2 RTL
//
// The barycentric weighting step of Moller-Trumbore: u = dot(tvec, pvec) * inv_det,
// v = dot(dir, qvec) * inv_det, t = dot(edge2, qvec) * inv_det all multiply a
// 3-vector by one shared fp32 scalar. Purely combinational — three parallel
// correctly-rounded HapiCore fp32 multiplies:
//   c_i = s * v_i
// Bit-exact vs the fp32 golden sobek_fp32.scale — see tb/test_scale.py.

module sobek_scale (
    input  logic [31:0] s,
    input  logic [31:0] v0, v1, v2,
    output logic [31:0] c0, c1, c2
);
    hapi_fp32_mul u_m0 (.a(s), .b(v0), .y(c0));
    hapi_fp32_mul u_m1 (.a(s), .b(v1), .y(c1));
    hapi_fp32_mul u_m2 (.a(s), .b(v2), .y(c2));
endmodule
