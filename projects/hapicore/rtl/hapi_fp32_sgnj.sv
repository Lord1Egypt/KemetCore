// HapiCore — fp32 sign-injection (fsgnj / fsgnjn / fsgnjx) — KemetCore Phase 2 RTL
//
// The RISC-V F-extension sign-manipulation ops: the result takes operand a's
// magnitude (its low 31 bits) with a sign bit derived from b:
//   op=00 fsgnj   y.sign = b.sign
//   op=01 fsgnjn  y.sign = ~b.sign
//   op=10 fsgnjx  y.sign = a.sign ^ b.sign   (e.g. fabs via fsgnjx a,a; fneg via fsgnjn)
// Purely bitwise — exact for every operand including NaN/Inf/zero (the magnitude
// bits, hence any NaN payload, are preserved unchanged).
//
// Verified bit-exact vs the golden fp32_sgnj — see tb/test_fp32_sgnj.py. Combinational.

module hapi_fp32_sgnj (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [1:0]  op,    // 00 fsgnj, 01 fsgnjn, 10 fsgnjx
    output logic [31:0] y
);
    logic sgn;
    always_comb begin
        case (op)
            2'b00:   sgn = b[31];
            2'b01:   sgn = ~b[31];
            2'b10:   sgn = a[31] ^ b[31];
            default: sgn = b[31];
        endcase
    end
    assign y = {sgn, a[30:0]};
endmodule
