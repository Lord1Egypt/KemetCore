// SobekCore — fp32 faceforward: orient a normal against the ray — Phase 2 RTL
//
// Shading-normal convention: if the geometric normal n faces the same way as the
// ray direction d (dot3(d,n) > 0), negate it so it points back toward the ray;
// otherwise pass it through. Purely combinational:
//   k   = dot3(d, n)                       (sobek_dot3)
//   flip = (k > 0)  in IEEE fp32 ordering  -> k positive, non-zero, non-NaN
//   r_i = flip ? -n_i : n_i                (exact fp32 sign flip)
// The flip predicate is exact: k[31]==0 (positive/+0), some magnitude bit set
// (excludes +0), and NOT a NaN (exponent all-ones with non-zero mantissa).
// Bit-exact vs the fp32 golden sobek_fp32.faceforward — see tb/test_faceforward.py.

module sobek_faceforward (
    input  logic [31:0] n0, n1, n2,
    input  logic [31:0] d0, d1, d2,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] k;
    logic        is_nan, flip;

    // k = dot3(d, n)
    sobek_dot3 u_dot (.a0(d0), .a1(d1), .a2(d2),
                      .b0(n0), .b1(n1), .b2(n2), .y(k));

    // k is NaN: exponent all ones and mantissa non-zero
    assign is_nan = (&k[30:23]) & (|k[22:0]);
    // k > 0: sign clear, some magnitude bit set (not +0), and not NaN
    assign flip = (~k[31]) & (|k[30:0]) & (~is_nan);

    assign r0 = flip ? {~n0[31], n0[30:0]} : n0;
    assign r1 = flip ? {~n1[31], n1[30:0]} : n1;
    assign r2 = flip ? {~n2[31], n2[30:0]} : n2;
endmodule
