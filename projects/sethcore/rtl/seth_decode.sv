// SethCore — RV32IM main control decoder (KemetCore Phase 2 RTL, combinational)
//
// Decodes an instruction's opcode (and funct7 for the M-extension) into the
// datapath control word that steers the rest of the pipeline. Output signals:
//   reg_write   : instruction writes rd
//   alu_src_imm : ALU operand B is the immediate (else rs2)
//   a_src_pc    : ALU operand A is the PC (auipc)
//   mem_read    : load
//   mem_write   : store
//   branch      : conditional branch
//   jump        : unconditional jump (jal/jalr)
//   jalr        : jump target is rs1+imm (else pc+imm)
//   is_mdu      : R-type M-extension (use the mul/div unit, not the ALU)
//   wb_sel[1:0] : writeback source — 0 ALU/MDU, 1 load data, 2 PC+4 (link), 3 imm (LUI)
// Unknown / system opcodes decode to all-zero: an inert no-op (no reg/mem write,
// no control transfer).
//
// Bit-exact against golden.decode_ctrl — see tb/test_decode.py. No latches.

module seth_decode (
    input  logic [31:0] ins,
    output logic        reg_write,
    output logic        alu_src_imm,
    output logic        a_src_pc,
    output logic        mem_read,
    output logic        mem_write,
    output logic        branch,
    output logic        jump,
    output logic        jalr,
    output logic        is_mdu,
    output logic [1:0]  wb_sel
);
    logic [6:0] op, f7;
    assign op = ins[6:0];
    assign f7 = ins[31:25];

    always_comb begin
        reg_write   = 1'b0;
        alu_src_imm = 1'b0;
        a_src_pc    = 1'b0;
        mem_read    = 1'b0;
        mem_write   = 1'b0;
        branch      = 1'b0;
        jump        = 1'b0;
        jalr        = 1'b0;
        is_mdu      = 1'b0;
        wb_sel      = 2'd0;
        case (op)
            7'h33: begin reg_write = 1'b1; is_mdu = (f7 == 7'h01); end            // R-type / M
            7'h13: begin reg_write = 1'b1; alu_src_imm = 1'b1; end                // I-type ALU
            7'h03: begin reg_write = 1'b1; alu_src_imm = 1'b1; mem_read = 1'b1; wb_sel = 2'd1; end  // load
            7'h23: begin alu_src_imm = 1'b1; mem_write = 1'b1; end                // store
            7'h63: begin branch = 1'b1; end                                      // branch
            7'h67: begin reg_write = 1'b1; alu_src_imm = 1'b1; jump = 1'b1; jalr = 1'b1; wb_sel = 2'd2; end  // jalr
            7'h6F: begin reg_write = 1'b1; jump = 1'b1; wb_sel = 2'd2; end        // jal
            7'h37: begin reg_write = 1'b1; wb_sel = 2'd3; end                    // lui
            7'h17: begin reg_write = 1'b1; a_src_pc = 1'b1; alu_src_imm = 1'b1; end  // auipc
            default: ; // system / unknown -> inert no-op
        endcase
    end
endmodule
