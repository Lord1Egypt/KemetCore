// SethCore — branch-condition unit (KemetCore Phase 2 RTL)
//
// Combinational evaluation of the RV32I conditional-branch test. Given funct3 and
// the two source registers, it asserts `taken` when the branch is satisfied. This
// is the datapath block the EX stage uses to decide whether to redirect the PC;
// it mirrors the golden branch_taken (projects/sethcore/golden/seth_rv32im.py).
//
//   funct3  insn   condition
//   000     beq    rs1 == rs2
//   001     bne    rs1 != rs2
//   100     blt    rs1 <  rs2   (signed)
//   101     bge    rs1 >= rs2   (signed)
//   110     bltu   rs1 <  rs2   (unsigned)
//   111     bgeu   rs1 >= rs2   (unsigned)
//
// funct3 010/011 are not valid branch encodings and read as not-taken. Combinational.
//
// Verified against the Python reference — see tb/test_branch.py.

module seth_branch (
    input  logic [2:0]  funct3,
    input  logic [31:0] rs1,
    input  logic [31:0] rs2,
    output logic        taken
);
    wire        eq   = (rs1 == rs2);
    wire        lt_s = ($signed(rs1) < $signed(rs2));
    wire        lt_u = (rs1 < rs2);

    always_comb begin
        case (funct3)
            3'b000: taken =  eq;     // beq
            3'b001: taken = ~eq;     // bne
            3'b100: taken =  lt_s;   // blt
            3'b101: taken = ~lt_s;   // bge
            3'b110: taken =  lt_u;   // bltu
            3'b111: taken = ~lt_u;   // bgeu
            default: taken = 1'b0;
        endcase
    end
endmodule
