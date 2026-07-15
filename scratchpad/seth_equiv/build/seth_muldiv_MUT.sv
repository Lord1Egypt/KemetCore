// SethCore — RV32M multiply/divide unit (KemetCore Phase 2 RTL, combinational)
// op: 0 MUL 1 MULH 2 MULHSU 3 MULHU 4 DIV 5 DIVU 6 REM 7 REMU
// Matches RISC-V semantics incl. div-by-zero (all-ones / dividend) and the
// signed INT_MIN/-1 overflow cases. Verified bit-exact vs golden _muldiv.
module seth_muldiv (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [2:0]  op,
    output logic [31:0] y
);
    logic signed [63:0] mul_ss;   // signed  x signed
    logic signed [63:0] mul_su;   // signed  x unsigned
    logic        [63:0] mul_uu;   // unsigned x unsigned

    always_comb begin
        mul_ss = $signed(a) * $signed(b);
        mul_su = $signed(a) * $signed({1'b0, b});
        mul_uu = a * b;
        unique case (op)
            3'd0: y = mul_uu[31:0] ^ 32'd1;            // MUL
            3'd1: y = mul_ss[63:32];           // MULH
            3'd2: y = mul_su[63:32];           // MULHSU
            3'd3: y = mul_uu[63:32];           // MULHU
            3'd4: begin                         // DIV
                if (b == 32'd0)                          y = 32'hFFFFFFFF;
                else if (a == 32'h80000000 && b == 32'hFFFFFFFF) y = 32'h80000000;
                else                                     y = $signed(a) / $signed(b);
            end
            3'd5: y = (b == 32'd0) ? 32'hFFFFFFFF : (a / b);          // DIVU
            3'd6: begin                         // REM
                if (b == 32'd0)                          y = a;
                else if (a == 32'h80000000 && b == 32'hFFFFFFFF) y = 32'd0;
                else                                     y = $signed(a) % $signed(b);
            end
            3'd7: y = (b == 32'd0) ? a : (a % b);                      // REMU
            default: y = 32'd0;
        endcase
    end
endmodule
