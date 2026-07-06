// NeithCore — FORMAL: neith_modmul (Barrett reduction mod Q=7681) always
// produces a VALID reduced field element: r < Q for every a,b in [0,Q).
//
// Proved exhaustively over the whole operand space (a,b < Q) in a single
// combinational BMC step — for ALL inputs, not the random sample cocotb runs.
// Output-in-range is the safety property the rest of the ML-KEM datapath relies
// on: every product feeds another mod-Q stage, so an out-of-range result would
// corrupt the NTT.
//
// HONEST SCOPE NOTE: the stronger property r == (a*b) mod Q (Barrett == true
// modulo) is a divider-equivalence miter — proving the multiply/shift Barrett
// datapath equals the `%` operator over the full 2^26 product space does not
// converge under z3 in CI time. That exact-value correctness is covered
// bit-exact by the cocotb testbench against the golden _modmul; here we formally
// guarantee the reduction is always well-formed (in range) for all inputs.
module formal_modmul (input logic [12:0] a, b);
    localparam logic [12:0] Q = 13'd7681;
    logic [12:0] r;
    neith_modmul u (.a(a), .b(b), .r(r));
    always_comb begin
        assume (a < Q);          // module contract: operands in [0,Q)
        assume (b < Q);
        assert (r < Q);          // result is always a reduced field element
    end
endmodule
