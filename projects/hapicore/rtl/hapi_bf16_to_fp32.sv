// HapiCore — bf16 -> fp32 widening convert (exact)
//
// bf16 shares fp32's sign and 8-bit exponent and holds the top 7 mantissa bits,
// so widening is exact and trivial: append 16 zero mantissa bits. Inf (zero
// mantissa) stays Inf and a bf16 NaN (nonzero 7-bit mantissa) stays a NaN, since
// the surviving mantissa bits remain nonzero.
//
//   y = {bf16, 16'b0}
//
// Verified bit-exact vs the golden bf16_to_fp32 over all 65536 patterns — see
// tb/test_bf16_to_fp32.py. Combinational only.

module hapi_bf16_to_fp32 (
    input  logic [15:0] a,     // bfloat16
    output logic [31:0] y      // IEEE-754 single
);
    assign y = {a, 16'd0};
endmodule
