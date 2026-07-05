// HapiCore — FORMAL: hapi_fp32_add commutativity over all 2^64 inputs.
// IEEE-754 add is commutative bit-exactly (canonical qNaN, symmetric align/round).
module formal_fp32_add (input logic [31:0] a, b);
    wire [31:0] y_ab, y_ba;
    hapi_fp32_add u_ab (.a(a), .b(b), .y(y_ab));
    hapi_fp32_add u_ba (.a(b), .b(a), .y(y_ba));
    always_comb assert (y_ab == y_ba);
endmodule
