// BastCore — FORMAL: bast_int8_mac accumulates a COMMUTATIVE product through the
// full signed 8x8->16->32 datapath — acc(a,b) == acc(b,a) in every reachable
// state (proved by k-induction), for all signed int8 operands and any control.
module formal_int8_mac (
    input logic clk, rst_n, en, clear,
    input logic signed [7:0] a, b
);
    logic signed [31:0] acc_ab, acc_ba;
    bast_int8_mac u_ab (.clk(clk),.rst_n(rst_n),.en(en),.clear(clear),.a(a),.b(b),.acc(acc_ab));
    bast_int8_mac u_ba (.clk(clk),.rst_n(rst_n),.en(en),.clear(clear),.a(b),.b(a),.acc(acc_ba));
    always_comb assert (acc_ab == acc_ba);
endmodule
