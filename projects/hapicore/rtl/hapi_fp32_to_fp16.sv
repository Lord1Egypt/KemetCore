// HapiCore — fp32 -> fp16 (IEEE half) narrowing convert, round-to-nearest-even
//
// Unlike bf16, fp16 has a different exponent width (5 vs 8), so the conversion
// rebiases the exponent (bias 127 -> 15) and handles overflow->Inf, gradual
// underflow to fp16 subnormals, and full underflow to signed zero. Rounding is
// round-half-to-even throughout. The unified method forms the 24-bit significand
// {1,mant} and rounds it onto the fp16 grid:
//   - normal result  (113 <= e32 <= 142): keep mant[22:13], round at bit 12.
//   - subnormal/zero  (e32 <= 112): right-shift the significand by (126 - e32)
//                                    with guard/round/sticky; a round-up to 2^10
//                                    promotes to the smallest normal.
//   - overflow        (e32 >= 143) and Inf -> +/-Inf; NaN -> quiet fp16 NaN.
//   - fp32 subnormal/zero (e32 == 0): magnitude << fp16 min -> signed zero.
//
// Verified bit-exact vs numpy float16 (correctly-rounded) — see tb/test_fp32_to_fp16.py.
// Combinational only.

module hapi_fp32_to_fp16 (
    input  logic [31:0] a,     // IEEE-754 single
    output logic [15:0] y      // IEEE-754 half (RNE)
);
    wire        sign = a[31];
    wire [7:0]  e32  = a[30:23];
    wire [22:0] m32  = a[22:0];
    wire [23:0] sig  = {1'b1, m32};          // implicit-1 significand

    // ---- normal path (113..142): keep top 10 fraction bits, round at bit 12 ---
    wire [7:0]  e16n   = e32 - 8'd112;        // 1..30 (all bits used below)
    wire [9:0]  fracn  = m32[22:13];
    wire        rnd_n  = m32[12];
    wire        stk_n  = |m32[11:0];
    wire        up_n   = rnd_n & (stk_n | fracn[0]);
    wire [10:0] fr_n   = {1'b0, fracn} + {10'b0, up_n};        // carry in bit 10
    wire [8:0]  e16n_r = {1'b0, e16n} + {8'b0, fr_n[10]};

    // ---- subnormal path (e32 <= 112): right shift sig by rsh = 126 - e32 -------
    wire [7:0]  rsh = 8'd126 - e32;          // >= 14 in this regime
    reg  [23:0] sh;
    reg         rbit, sbit;
    reg  [10:0] mant_sub;                     // 0..1024
    always_comb begin
        if (rsh >= 8'd25) begin
            sh   = 24'd0;
            rbit = 1'b0;
            sbit = |sig;                      // entire significand lost -> sticky
        end else begin
            sh   = sig >> rsh;
            rbit = sig[rsh[4:0] - 5'd1];
            sbit = (|(sig & ((24'd1 << (rsh - 8'd1)) - 24'd1))) | (|sh[23:10]);
        end
        mant_sub = {1'b0, sh[9:0]} + {10'b0, (rbit & (sbit | sh[0]))};
    end

    always_comb begin
        if (e32 == 8'hFF) begin
            y = {sign, 5'h1F, (m32 == 23'd0) ? 10'h000 : 10'h200};   // Inf / qNaN
        end else if (e32 == 8'd0) begin
            y = {sign, 15'h0000};                                    // fp32 subnormal/0
        end else if (e32 >= 8'd143) begin
            y = {sign, 5'h1F, 10'h000};                              // overflow -> Inf
        end else if (e32 >= 8'd113) begin
            if (e16n_r >= 9'd31) y = {sign, 5'h1F, 10'h000};         // rounded up to Inf
            else                 y = {sign, e16n_r[4:0], fr_n[9:0]};
        end else begin
            if (mant_sub == 11'd1024)     y = {sign, 5'd1, 10'd0};   // -> smallest normal
            else if (mant_sub == 11'd0)   y = {sign, 15'h0000};      // -> signed zero
            else                          y = {sign, 5'd0, mant_sub[9:0]};
        end
    end
endmodule
