// SethCore — registered P&R boundary top for seth_aluctl (KemetCore Phase 4 depth)
//
// seth_aluctl is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_aluctl is instantiated UNCHANGED.
module seth_aluctl_p4top (
    input  logic       clk,
    input  logic       rst,
    input  logic [6:0] opcode_in,
    input  logic [2:0] funct3_in,
    input  logic [6:0] funct7_in,
    output logic [3:0] alu_op_out
);
    logic [6:0] opcode_q;
    logic [2:0] funct3_q;
    logic [6:0] funct7_q;
    logic [3:0] alu_op_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            opcode_q <= 7'd0;
            funct3_q <= 3'd0;
            funct7_q <= 7'd0;
        end else begin
            opcode_q <= opcode_in;
            funct3_q <= funct3_in;
            funct7_q <= funct7_in;
        end
    end

    seth_aluctl u_core (
        .opcode(opcode_q),
        .funct3(funct3_q),
        .funct7(funct7_q),
        .alu_op(alu_op_c)
    );

    always_ff @(posedge clk) begin
        if (rst) alu_op_out <= 4'd0;
        else     alu_op_out <= alu_op_c;
    end
endmodule
