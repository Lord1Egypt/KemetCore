// HapiCore — fp16 sign-injection (fsgnj / fsgnjn / fsgnjx) — KemetCore Phase 2 RTL
//
// RISC-V F-extension sign-injection at half precision (the fp16 analogue of
// hapi_fp32_sgnj): a's magnitude with a sign derived from b.
//   op 0 fsgnj  -> b.sign;  1 fsgnjn -> ~b.sign;  2 fsgnjx -> a.sign ^ b.sign.
// Purely combinational and exact (no rounding). Bit-exact vs golden fp16_sgnj.

module hapi_fp16_sgnj (
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic [1:0]  op,
    output logic [15:0] y
);
    logic sgn;
    always_comb begin
        case (op)
            2'd0:    sgn = b[15];
            2'd1:    sgn = ~b[15];
            default: sgn = a[15] ^ b[15];   // fsgnjx
        endcase
    end
    assign y = {sgn, a[14:0]};
endmodule
