// NeithCore — modular multiplier mod Q = 7681 (KemetCore Phase 2 RTL)
//
// Single-cycle combinational a*b mod 7681 via Barrett reduction. 7681 is the
// NTT-friendly modulus used by the golden (q-1 = 2^9*15, so a 2N-th root exists);
// it is the workhorse of the NeithCore lattice-KEM NTT.
//
// Barrett: with inputs a,b in [0,Q) the product P = a*b < Q^2 < 2^26. Using
// mu = floor(2^26 / Q) = 8736, the quotient estimate q_est = floor(P*mu / 2^26)
// is at most 2 below the true quotient, so the remainder P - q_est*Q is < 3Q and
// at most two conditional subtractions of Q restore the canonical residue. A third
// (no-op) subtraction is unrolled for margin.
//
// Bit-exact against (a*b) % 7681 — see tb/test_modmul.py.
// Yosys-portable: no int'() casts, all operands width-matched explicitly.

module neith_modmul (
    input  logic [12:0] a,   // operand, assumed < Q
    input  logic [12:0] b,   // operand, assumed < Q
    output logic [12:0] r    // (a*b) mod Q
);
    localparam logic [26:0] Q  = 27'd7681;
    localparam logic [26:0] MU = 27'd8736;   // floor(2^26 / Q)

    logic [25:0] p;          // a*b  (< 2^26)
    logic [39:0] pm;         // p*mu (< 2^40)
    logic [13:0] qest;       // floor(p*mu / 2^26)
    logic [26:0] qq;         // qest * Q
    logic [26:0] r0, r1, r2, r3;

    assign p    = {13'b0, a} * {13'b0, b};
    assign pm   = {14'b0, p} * {26'b0, MU[13:0]};
    assign qest = pm[39:26];
    assign qq   = {13'b0, qest} * Q;
    assign r0   = {1'b0, p} - qq;                 // >= 0, < 3Q

    assign r1 = (r0 >= Q) ? (r0 - Q) : r0;
    assign r2 = (r1 >= Q) ? (r1 - Q) : r1;
    assign r3 = (r2 >= Q) ? (r2 - Q) : r2;
    assign r  = r3[12:0];
endmodule
