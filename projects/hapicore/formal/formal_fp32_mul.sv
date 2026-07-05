// HapiCore — FORMAL properties for hapi_fp32_mul (KemetCore Phase 5, formal)
//
// Exhaustive proofs over the full 2^64 input space (what random cocotb cannot
// cover). Discharged by yosys write_smt2 + yosys-smtbmc + z3 — see run_formal.sh.
module formal_fp32_mul (input logic [31:0] a, b);
    wire [31:0] y_ab, y_ba;
    hapi_fp32_mul u_ab (.a(a), .b(b), .y(y_ab));
    hapi_fp32_mul u_ba (.a(b), .b(a), .y(y_ba));

    // P1: commutativity — a*b is bit-identical to b*a for ALL inputs (the
    // multiplier canonicalises NaN to qNaN and all specials are symmetric).
    always_comb assert (y_ab == y_ba);

    // P2: sign is exactly sign_a XOR sign_b whenever the result is not NaN.
    wire is_nan = (y_ab[30:23] == 8'hFF) && (y_ab[22:0] != 0);
    always_comb if (!is_nan) assert (y_ab[31] == (a[31] ^ b[31]));
endmodule
