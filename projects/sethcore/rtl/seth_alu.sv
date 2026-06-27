// SethCore — RV32 integer ALU (KemetCore Phase 2 RTL, combinational)
// op: 0 ADD 1 SUB 2 SLL 3 SLT 4 SLTU 5 XOR 6 SRL 7 SRA 8 OR 9 AND
// Verified bit-exact against the golden Cpu._alu_r — see tb/test_alu.py.
module seth_alu (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [3:0]  op,
    output logic [31:0] y
);
    always_comb begin
        unique case (op)
            4'd0: y = a + b;
            4'd1: y = a - b;
            4'd2: y = a << b[4:0];
            4'd3: y = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            4'd4: y = (a < b) ? 32'd1 : 32'd0;
            4'd5: y = a ^ b;
            4'd6: y = a >> b[4:0];
            4'd7: y = $signed(a) >>> b[4:0];
            4'd8: y = a | b;
            4'd9: y = a & b;
            default: y = 32'd0;
        endcase
    end
endmodule
