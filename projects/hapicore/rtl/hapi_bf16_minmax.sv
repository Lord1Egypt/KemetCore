// HapiCore — bf16 minimum / maximum (fmin / fmax) — KemetCore Phase 2 RTL
//
// RISC-V fmin/fmax at bfloat16 (1/8/7): one NaN -> other operand, both NaN ->
// canonical qNaN 0x7FC0, else smaller/larger with -0.0 < +0.0 via the 16-bit
// monotonic key k = x ^ (x[15] ? 0xFFFF : 0x8000). op 0 fmin, 1 fmax.
// Bit-exact vs golden bf16_minmax. Combinational.

module hapi_bf16_minmax (
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic        op,
    output logic [15:0] y
);
    wire a_nan = (a[14:7] == 8'hFF) && (a[6:0] != 7'd0);
    wire b_nan = (b[14:7] == 8'hFF) && (b[6:0] != 7'd0);
    wire [15:0] ka = a ^ (a[15] ? 16'hFFFF : 16'h8000);
    wire [15:0] kb = b ^ (b[15] ? 16'hFFFF : 16'h8000);
    wire        a_le_b = (ka <= kb);
    wire [15:0] picked = op ? (a_le_b ? b : a) : (a_le_b ? a : b);
    always_comb begin
        if (a_nan && b_nan) y = 16'h7FC0;
        else if (a_nan)     y = b;
        else if (b_nan)     y = a;
        else                y = picked;
    end
endmodule
