// P&R wrapper for NeithCore modmul (KemetCore Phase 4 P&R)
//
// Wraps the combinational neith_modmul datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module neith_modmul_p4top (
    input  logic        clk,
    input  logic [12:0] a,
    input  logic [12:0] b,
    output logic [12:0] r
);
    logic [12:0] a_reg, b_reg;
    logic [12:0] r_comb;

    always_ff @(posedge clk) begin
        a_reg <= a;
        b_reg <= b;
        r     <= r_comb;
    end

    neith_modmul u_core (
        .a(a_reg),
        .b(b_reg),
        .r(r_comb)
    );
endmodule
