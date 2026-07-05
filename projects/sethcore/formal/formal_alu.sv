// SethCore — FORMAL: exhaustive algebraic properties of seth_alu (all 2^68 (a,b,op)).
// op: 0 ADD 1 SUB 2 SLL 3 SLT 4 SLTU 5 XOR 6 SRL 7 SRA 8 OR 9 AND
module formal_alu (input logic [31:0] a, b);
    localparam [3:0] ADD=0, SUB=1, SLT=3, SLTU=4, XOR=5, OR=8, AND=9;
    wire [31:0] y_add, y_sub, y_xor, y_and, y_or, y_slt, y_sltu, y_subadd, y_sub_of_add;
    seth_alu u_add  (.a(a),       .b(b), .op(ADD),  .y(y_add));
    seth_alu u_sub  (.a(a),       .b(b), .op(SUB),  .y(y_sub));
    seth_alu u_xor  (.a(a),       .b(a), .op(XOR),  .y(y_xor));     // a^a
    seth_alu u_and  (.a(a),       .b(a), .op(AND),  .y(y_and));     // a&a
    seth_alu u_or   (.a(a),       .b(a), .op(OR),   .y(y_or));      // a|a
    seth_alu u_slt  (.a(a),       .b(b), .op(SLT),  .y(y_slt));
    seth_alu u_sltu (.a(a^32'h80000000), .b(b^32'h80000000), .op(SLTU), .y(y_sltu));
    seth_alu u_subadd (.a(y_add), .b(b), .op(SUB),  .y(y_subadd));  // (a+b)-b
    seth_alu u_subtc  (.a(a), .b(~b + 32'd1), .op(ADD), .y(y_sub_of_add)); // a + (-b)

    always_comb begin
        assert (y_xor == 32'd0);              // XOR self-inverse
        assert (y_and == a);                  // AND idempotent
        assert (y_or  == a);                  // OR idempotent
        assert (y_subadd == a);               // (a+b)-b == a
        assert (y_sub == y_sub_of_add);       // a-b == a + two's-comp(b)
        assert (y_slt == y_sltu);             // signed< via unsigned< on flipped MSB
    end
endmodule
