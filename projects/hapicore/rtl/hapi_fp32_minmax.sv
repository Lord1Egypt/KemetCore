// HapiCore — fp32 minimum / maximum (fmin / fmax) — KemetCore Phase 2 RTL
//
// RISC-V F-extension fmin/fmax semantics:
//   - if exactly one operand is NaN, return the OTHER (non-NaN) operand;
//   - if BOTH are NaN, return the canonical quiet NaN 0x7FC00000;
//   - otherwise return the smaller (fmin) / larger (fmax), with -0.0 < +0.0.
// Ordering uses a monotonic total-order key: mapping the IEEE bits with
// k = x ^ (x[31] ? 0xFFFFFFFF : 0x80000000) makes unsigned compare equal the real
// ordering (and places -0 just below +0), so no arithmetic comparator is needed.
//
// op = 0 -> fmin, op = 1 -> fmax. Verified bit-exact vs golden fp32_minmax —
// see tb/test_fp32_minmax.py. Combinational.

module hapi_fp32_minmax (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic        op,    // 0 = fmin, 1 = fmax
    output logic [31:0] y
);
    wire a_nan = (a[30:23] == 8'hFF) && (a[22:0] != 23'd0);
    wire b_nan = (b[30:23] == 8'hFF) && (b[22:0] != 23'd0);

    wire [31:0] ka = a ^ (a[31] ? 32'hFFFF_FFFF : 32'h8000_0000);
    wire [31:0] kb = b ^ (b[31] ? 32'hFFFF_FFFF : 32'h8000_0000);
    wire        a_le_b = (ka <= kb);

    wire [31:0] smaller = a_le_b ? a : b;
    wire [31:0] larger  = a_le_b ? b : a;
    wire [31:0] picked  = op ? larger : smaller;

    always_comb begin
        if (a_nan && b_nan) y = 32'h7FC0_0000;   // canonical quiet NaN
        else if (a_nan)     y = b;
        else if (b_nan)     y = a;
        else                y = picked;
    end
endmodule
