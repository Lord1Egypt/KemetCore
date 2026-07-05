// SethCore — registered P&R boundary top for seth_alu (KemetCore Phase 4 depth)
//
// seth_alu (the RV32I ALU: add/sub/sll/slt/sltu/xor/srl/sra/or/and) is purely
// combinational. This wrapper latches the operands + op select, drives the
// verified ALU, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_alu is instantiated UNCHANGED.
module seth_alu_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] a_in,
    input  logic [31:0] b_in,
    input  logic [3:0]  op_in,
    output logic [31:0] y_out
);
    logic [31:0] a_q, b_q, y_c;
    logic [3:0]  op_q;

    always_ff @(posedge clk) begin
        if (rst) begin a_q <= 32'd0; b_q <= 32'd0; op_q <= 4'd0; end
        else     begin a_q <= a_in;  b_q <= b_in;  op_q <= op_in; end
    end

    seth_alu u_core (.a(a_q), .b(b_q), .op(op_q), .y(y_c));

    always_ff @(posedge clk) begin
        if (rst) y_out <= 32'd0;
        else     y_out <= y_c;
    end
endmodule
