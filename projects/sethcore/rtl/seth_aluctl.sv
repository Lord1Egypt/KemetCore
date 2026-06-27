// SethCore — RV32 ALU control decoder (KemetCore Phase 2 RTL, combinational)
//
// Maps an instruction's (opcode, funct3, funct7) to the 4-bit ALU select consumed
// by seth_alu (0 ADD, 1 SUB, 2 SLL, 3 SLT, 4 SLTU, 5 XOR, 6 SRL, 7 SRA, 8 OR,
// 9 AND). This is the bridge between instruction decode and the ALU.
//
//   R-type (0x33): decode by funct3; funct7=0x20 selects SUB (f3=0) / SRA (f3=5);
//                  the M-extension (funct7=0x01) does not use this ALU -> ADD.
//   I-type  (0x13): decode by funct3; SRLI/SRAI split on funct7=0x20 (ins[30]).
//   everything else (loads/stores/branch/jalr/lui/auipc/jal/system): address or
//                  PC arithmetic only -> ADD.
//
// Bit-exact against golden.decode_aluop — see tb/test_aluctl.py. Exhaustively
// verifiable (opcode x funct3 x funct7 = 2^17 inputs). No latches.

module seth_aluctl (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,
    output logic [3:0] alu_op
);
    logic [3:0] rtype_op;
    always_comb begin
        unique case (funct3)
            3'h0: rtype_op = (funct7 == 7'h20) ? 4'd1 : 4'd0;   // SUB / ADD
            3'h1: rtype_op = 4'd2;                              // SLL
            3'h2: rtype_op = 4'd3;                              // SLT
            3'h3: rtype_op = 4'd4;                              // SLTU
            3'h4: rtype_op = 4'd5;                              // XOR
            3'h5: rtype_op = (funct7 == 7'h20) ? 4'd7 : 4'd6;   // SRA / SRL
            3'h6: rtype_op = 4'd8;                              // OR
            3'h7: rtype_op = 4'd9;                              // AND
        endcase
    end

    always_comb begin
        if (opcode == 7'h33)
            alu_op = (funct7 == 7'h01) ? 4'd0 : rtype_op;       // M-ext -> ADD
        else if (opcode == 7'h13)
            // I-type: same funct3 map, but only the shift forms look at funct7
            alu_op = (funct3 == 3'h0) ? 4'd0 : rtype_op;        // ADDI never SUB
        else
            alu_op = 4'd0;                                      // address / PC add
    end
endmodule
