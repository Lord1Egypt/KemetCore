// SobekCore — FORMAL: sobek_scale (scalar*vector, s*v) MULTIPLY-COMMUTATIVITY.
// Each output lane c_i = s * v_i must equal v_i * s bit-exactly, for all fp32 s
// and v (subnormals, Inf, NaN, signed zero). Proved exhaustively in one
// combinational BMC step against a swapped-operand reference multiplier.
//
// sobek_scale is the mul-only member of the ray-math library (three independent
// hapi_fp32_mul, no adds), so its equivalence miter is tractable for z3.
//
// HONEST SCOPE NOTE: the add-bearing ray-math ops (dot3, cross, normalize, ...)
// would need an fp32-adder equivalence miter that does not converge under z3 in
// CI time; their bit-exact correctness is covered by the cocotb testbenches vs
// the golden sobek_fp32. Here we formally prove the scalar-multiply datapath.
module formal_scale (input logic [31:0] s, v0, v1, v2);
    wire [31:0] c0, c1, c2;      // scale outputs: c_i = s * v_i
    wire [31:0] r0, r1, r2;      // reference:     r_i = v_i * s
    sobek_scale  u (.s(s), .v0(v0), .v1(v1), .v2(v2), .c0(c0), .c1(c1), .c2(c2));
    hapi_fp32_mul m0 (.a(v0), .b(s), .y(r0));
    hapi_fp32_mul m1 (.a(v1), .b(s), .y(r1));
    hapi_fp32_mul m2 (.a(v2), .b(s), .y(r2));
    always_comb begin
        assert (c0 == r0);
        assert (c1 == r1);
        assert (c2 == r2);
    end
endmodule
