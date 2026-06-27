// SethCore — RV32 immediate generator (KemetCore Phase 2 RTL)
//
// Combinational decode of the instruction immediate, selected by opcode/format
// and sign-extended where the ISA requires it. This is the first datapath block
// of the RV32IM pipeline (feeds the ALU's second operand, branch/jump targets,
// and address generation). The five RISC-V immediate encodings:
//   I (op 0x13 ALU-imm / 0x03 load / 0x67 jalr) : ins[31:20]                      (12b, sext)
//   S (op 0x23 store)                            : ins[31:25],ins[11:7]           (12b, sext)
//   B (op 0x63 branch)                           : ins[31],ins[7],ins[30:25],ins[11:8],0   (13b, sext)
//   U (op 0x37 lui / 0x17 auipc)                 : ins[31:12],{12'b0}             (no extend)
//   J (op 0x6F jal)                              : ins[31],ins[19:12],ins[20],ins[30:21],0 (21b, sext)
// R-type and system instructions carry no immediate -> 0.
//
// Bit-exact against golden.decode_imm — see tb/test_imm.py. Yosys-portable, no latches.

module seth_imm (
    input  logic [31:0] ins,
    output logic [31:0] imm
);
    logic [6:0] op;
    assign op = ins[6:0];

    logic [11:0] i_imm, s_imm;
    logic [12:0] b_imm;
    logic [20:0] j_imm;
    assign i_imm = ins[31:20];
    assign s_imm = {ins[31:25], ins[11:7]};
    assign b_imm = {ins[31], ins[7], ins[30:25], ins[11:8], 1'b0};
    assign j_imm = {ins[31], ins[19:12], ins[20], ins[30:21], 1'b0};

    always_comb begin
        case (op)
            7'h13, 7'h03, 7'h67: imm = {{20{i_imm[11]}}, i_imm};       // I-type
            7'h23:               imm = {{20{s_imm[11]}}, s_imm};       // S-type
            7'h63:               imm = {{19{b_imm[12]}}, b_imm};       // B-type
            7'h37, 7'h17:        imm = {ins[31:12], 12'b0};            // U-type
            7'h6F:               imm = {{11{j_imm[20]}}, j_imm};       // J-type
            default:             imm = 32'b0;                          // R-type / system
        endcase
    end
endmodule
