// SobekCore — FORMAL: sobek_dot3 is commutative over all inputs (each lane
// product a_i*b_i commutes and the add-chain order is preserved).
module formal_dot3 (input logic [31:0] a0,a1,a2,b0,b1,b2);
    wire [31:0] y_ab, y_ba;
    sobek_dot3 u_ab (.a0(a0),.a1(a1),.a2(a2),.b0(b0),.b1(b1),.b2(b2),.y(y_ab));
    sobek_dot3 u_ba (.a0(b0),.a1(b1),.a2(b2),.b0(a0),.b1(a1),.b2(a2),.y(y_ba));
    always_comb assert (y_ab == y_ba);
endmodule
