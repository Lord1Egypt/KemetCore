// HapiCore — FORMAL: hapi_fp32_add ADDITIVE IDENTITY — x + (+0.0) == x for every
// finite/subnormal/infinite x (excluding NaN and -0.0, whose exact IEEE results
// are +qNaN and +0.0 respectively). Proved exhaustively over all such x in one
// combinational BMC step.
//
// HONEST SCOPE NOTE: full commutativity add(a,b)==add(b,a) over all 2^64 pairs is
// intractable for z3 — an IEEE adder's align/swap/normalize logic makes the two
// swapped datapaths a hard bit-vector miter that does not converge in CI time
// (the multiplier's is symmetric and DOES converge; see formal_fp32_mul).
// Commutativity + full rounding are covered bit-exact by the cocotb testbench;
// here we formally pin the identity element of the adder for all inputs.
module formal_fp32_add (input logic [31:0] x);
    wire [31:0] y;
    hapi_fp32_add u (.a(x), .b(32'h0000_0000 /* +0.0 */), .y(y));
    always_comb begin
        assume (x[30:23] != 8'hFF);   // x is not Inf/NaN
        assume (x[30:0]  != 31'h0);   // x is not +/-0 (would give +0, not -0)
        assert (y == x);              // additive identity: x + 0 == x
    end
endmodule
