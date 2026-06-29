// HapiCore — fp32 -> bf16 narrowing convert (round-to-nearest-even)
//
// The mixed-precision downcast: rounds a 32-bit IEEE-754 single to a 16-bit
// bfloat16 (8 exponent / 7 mantissa), ties-to-even. bf16 shares fp32's 8-bit
// exponent, so a finite value is exactly the RNE rounding of fp32 at bit 16:
//
//   y = (a + 0x7FFF + a[16]) >> 16
//
// The 0x7FFF half-ulp bias plus the destination-lsb (a[16]) term implement
// round-half-to-even; carries propagate naturally into the exponent, so a finite
// value that rounds up past the bf16 maximum becomes +/-Inf. Inf passes through
// unchanged. A NaN is preserved as a canonical quiet bf16 NaN (sign + 0x7FC0)
// rather than being allowed to collapse to Inf when its surviving payload bits
// are zero.
//
// Verified against the Python golden fp32_to_bf16 — see tb/test_fp32_to_bf16.py.
// Combinational only.

module hapi_fp32_to_bf16 (
    input  logic [31:0] a,     // IEEE-754 single
    output logic [15:0] y      // bfloat16 (RNE)
);
    wire        is_nan  = (a[30:23] == 8'hFF) && (a[22:0] != 23'd0);
    wire [31:0] rounded = a + 32'h0000_7FFF + {31'b0, a[16]};
    assign y = is_nan ? {a[31], 15'h7FC0} : rounded[31:16];
endmodule
