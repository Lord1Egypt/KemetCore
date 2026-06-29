// HapiCore — fp16 (IEEE half) -> fp32 widening convert (exact)
//
// Every fp16 value is exactly representable in fp32, so this upcast is lossless
// (no rounding). It rebiases the exponent (15 -> 127) and normalises fp16
// subnormals into fp32 normals:
//   - normal   (1 <= e16 <= 30): e32 = e16 + 112, mant = m16 << 13.
//   - subnormal (e16 == 0, m16 != 0): value = m16 * 2^-24; normalise by the
//     leading-zero count lz of the 10-bit mantissa: e32 = 127 - 14 - lz, and the
//     mantissa is left-shifted to drop the implicit 1.
//   - zero     (e16 == 0, m16 == 0) -> signed zero.
//   - Inf/NaN  (e16 == 0x1F): exponent 0xFF, mantissa = m16 << 13 (Inf stays Inf,
//     NaN stays NaN with its payload preserved in the high mantissa bits).
//
// Verified bit-exact vs numpy (float16->float32) — see tb/test_fp16_to_fp32.py.
// Combinational only.

module hapi_fp16_to_fp32 (
    input  logic [15:0] a,     // IEEE-754 half
    output logic [31:0] y      // IEEE-754 single
);
    wire        sign = a[15];
    wire [4:0]  e16  = a[14:10];
    wire [9:0]  m16  = a[9:0];

    // leading-zero count of the 10-bit subnormal mantissa (0..9; 10 if zero)
    logic [3:0] lz;
    always_comb begin
        casez (m16)
            10'b1?????????: lz = 4'd0;
            10'b01????????: lz = 4'd1;
            10'b001???????: lz = 4'd2;
            10'b0001??????: lz = 4'd3;
            10'b00001?????: lz = 4'd4;
            10'b000001????: lz = 4'd5;
            10'b0000001???: lz = 4'd6;
            10'b00000001??: lz = 4'd7;
            10'b000000001?: lz = 4'd8;
            10'b0000000001: lz = 4'd9;
            default:        lz = 4'd10;   // m16 == 0
        endcase
    end

    // subnormal normalisation: shift the mantissa left so the leading 1 is dropped
    wire [9:0]  sub_shift = m16 << (lz + 4'd1);          // implicit-1 removed
    wire [22:0] sub_mant  = {sub_shift, 13'd0};
    wire [7:0]  sub_exp   = 8'd112 - {4'd0, lz};         // (1-15)+127-lz = 112-lz

    always_comb begin
        if (e16 == 5'h1F) begin
            y = {sign, 8'hFF, m16, 13'd0};                       // Inf / NaN
        end else if (e16 == 5'd0) begin
            if (m16 == 10'd0) y = {sign, 31'd0};                 // signed zero
            else              y = {sign, sub_exp, sub_mant};      // subnormal -> normal
        end else begin
            y = {sign, ({3'd0, e16} + 8'd112), m16, 13'd0};      // normal
        end
    end
endmodule
