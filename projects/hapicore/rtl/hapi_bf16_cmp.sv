// HapiCore — bf16 compare (feq / flt / fle) — KemetCore Phase 2 RTL
//
// RISC-V compare at bfloat16 (1/8/7): op 0 feq, 1 flt, 2 fle -> 1-bit. Any NaN
// -> 0; +0 == -0. Ordering via the 16-bit monotonic key, both-zero forced equal.
// Bit-exact vs golden bf16_cmp. Combinational.

module hapi_bf16_cmp (
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic [1:0]  op,
    output logic        y
);
    wire a_nan = (a[14:7] == 8'hFF) && (a[6:0] != 7'd0);
    wire b_nan = (b[14:7] == 8'hFF) && (b[6:0] != 7'd0);
    wire any_nan = a_nan || b_nan;
    wire both_zero = (a[14:0] == 15'd0) && (b[14:0] == 15'd0);
    wire [15:0] ka = a ^ (a[15] ? 16'hFFFF : 16'h8000);
    wire [15:0] kb = b ^ (b[15] ? 16'hFFFF : 16'h8000);
    wire eqv = both_zero || (a == b);
    wire ltv = (ka < kb) && !both_zero;
    always_comb begin
        if (any_nan) y = 1'b0;
        else case (op)
            2'd0:    y = eqv;
            2'd1:    y = ltv;
            default: y = ltv || eqv;
        endcase
    end
endmodule
