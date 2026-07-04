// HapiCore — fp16 minimum / maximum (fmin / fmax) — KemetCore Phase 2 RTL
//
// RISC-V F-extension fmin/fmax semantics at half precision (the fp16 analogue of
// hapi_fp32_minmax):
//   - if exactly one operand is NaN, return the OTHER (non-NaN) operand;
//   - if BOTH are NaN, return the canonical quiet NaN 0x7E00;
//   - otherwise return the smaller (fmin) / larger (fmax), with -0.0 < +0.0.
// Ordering uses a monotonic total-order key k = x ^ (x[15] ? 0xFFFF : 0x8000) so
// an unsigned compare equals the real ordering (-0 just below +0).
//
// op = 0 -> fmin, op = 1 -> fmax. Bit-exact vs golden fp16_minmax. Combinational.

module hapi_fp16_minmax (
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic        op,    // 0 = fmin, 1 = fmax
    output logic [15:0] y
);
    wire a_nan = (a[14:10] == 5'h1F) && (a[9:0] != 10'd0);
    wire b_nan = (b[14:10] == 5'h1F) && (b[9:0] != 10'd0);

    wire [15:0] ka = a ^ (a[15] ? 16'hFFFF : 16'h8000);
    wire [15:0] kb = b ^ (b[15] ? 16'hFFFF : 16'h8000);
    wire        a_le_b = (ka <= kb);

    wire [15:0] smaller = a_le_b ? a : b;
    wire [15:0] larger  = a_le_b ? b : a;
    wire [15:0] picked  = op ? larger : smaller;

    always_comb begin
        if (a_nan && b_nan) y = 16'h7E00;   // canonical quiet NaN
        else if (a_nan)     y = b;
        else if (b_nan)     y = a;
        else                y = picked;
    end
endmodule
