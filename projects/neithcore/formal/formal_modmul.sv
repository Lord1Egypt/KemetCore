// NeithCore — FORMAL: neith_modmul Barrett reduction is correct for ALL a,b < Q.
// Proves r == (a*b) mod 7681 exhaustively (7681^2 ~ 59M cases) + range r < Q +
// commutativity — what random cocotb only samples.
module formal_modmul (input logic [12:0] a, b);
    localparam [26:0] Q = 27'd7681;
    wire [12:0] r, r_swap;
    neith_modmul u    (.a(a), .b(b), .r(r));
    neith_modmul u_sw (.a(b), .b(a), .r(r_swap));
    wire [26:0] prod   = {14'd0, a} * {14'd0, b};
    wire [26:0] golden = prod % Q;
    always_comb begin
        assume (a < Q[12:0]);            // module contract: operands in [0,Q)
        assume (b < Q[12:0]);
        assert (r == golden[12:0]);      // Barrett == true modulo
        assert (r < Q[12:0]);            // result is reduced
        assert (r == r_swap);            // commutativity
    end
endmodule
