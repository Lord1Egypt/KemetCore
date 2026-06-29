// SethCore — Zicsr CSR datapath unit (KemetCore Phase 2 RTL)
//
// Combinational datapath for the six Zicsr instructions, mirroring the golden
// csr_op (projects/sethcore/golden/seth_rv32im.py). Given the current CSR value
// and the instruction's funct3 + source operand, it produces the value written
// back to rd (always the OLD csr value) and the next CSR value plus its write
// enable.
//
//   funct3  insn     operand         csr_out          csr_we
//   001     csrrw    rs1             operand          1
//   010     csrrs    rs1             csr | operand    operand != 0   (rs1 != x0)
//   011     csrrc    rs1             csr & ~operand   operand != 0
//   101     csrrwi   uimm[4:0]       operand          1
//   110     csrrsi   uimm[4:0]       csr | operand    operand != 0
//   111     csrrci   uimm[4:0]       csr & ~operand   operand != 0
//
// funct3[2] selects the immediate forms (operand = zero-extended uimm); funct3[1:0]
// selects RW/RS/RC. Per spec, CSRRS/CSRRC with a zero operand perform no write (so
// no write side effects); CSRRW always writes. rd always receives the old CSR value
// (the rd==x0 read-suppression is the integrating core's concern, not this unit's).
//
// Verified against the Python reference — see tb/test_csr.py. Combinational only.

module seth_csr (
    input  logic [2:0]  funct3,
    input  logic [31:0] csr_in,
    input  logic [31:0] rs1,
    input  logic [4:0]  zimm,
    output logic [31:0] rd_val,
    output logic [31:0] csr_out,
    output logic        csr_we
);
    wire        is_imm  = funct3[2];
    wire [31:0] operand = is_imm ? {27'd0, zimm} : rs1;

    assign rd_val = csr_in;

    always_comb begin
        case (funct3[1:0])
            2'b01: begin csr_out = operand;            csr_we = 1'b1;            end // RW
            2'b10: begin csr_out = csr_in |  operand;  csr_we = (operand != 0);  end // RS
            2'b11: begin csr_out = csr_in & ~operand;  csr_we = (operand != 0);  end // RC
            default: begin csr_out = csr_in;           csr_we = 1'b0;            end
        endcase
    end
endmodule
