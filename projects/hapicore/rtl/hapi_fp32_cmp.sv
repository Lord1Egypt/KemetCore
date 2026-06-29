// HapiCore — fp32 comparison (feq / flt / fle) — KemetCore Phase 2 RTL
//
// Scalar RISC-V F-extension compares producing a 1-bit (integer) result:
//   op=00 feq  a == b
//   op=01 flt  a <  b
//   op=10 fle  a <= b
// IEEE rules: any NaN operand makes every compare false; +0.0 equals -0.0 (so flt
// of -0,+0 is false). Ordered compares use the monotonic total-order key
// (x ^ (x[31]?0xFFFFFFFF:0x80000000)), with zeros forced equal.
//
// Verified bit-exact vs golden fp32_cmp — see tb/test_fp32_cmp.py. Combinational.

module hapi_fp32_cmp (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [1:0]  op,    // 00 feq, 01 flt, 10 fle
    output logic        y
);
    wire a_nan = (a[30:23] == 8'hFF) && (a[22:0] != 23'd0);
    wire b_nan = (b[30:23] == 8'hFF) && (b[22:0] != 23'd0);
    wire nan   = a_nan | b_nan;

    wire both_zero = ((a[30:0] == 31'd0) && (b[30:0] == 31'd0));
    wire [31:0] ka = a ^ (a[31] ? 32'hFFFF_FFFF : 32'h8000_0000);
    wire [31:0] kb = b ^ (b[31] ? 32'hFFFF_FFFF : 32'h8000_0000);

    wire eqv = both_zero | (a == b);
    wire ltv = (ka < kb) & ~both_zero;

    always_comb begin
        case (op)
            2'b00:   y = ~nan & eqv;            // feq
            2'b01:   y = ~nan & ltv;            // flt
            2'b10:   y = ~nan & (ltv | eqv);    // fle
            default: y = 1'b0;
        endcase
    end
endmodule
