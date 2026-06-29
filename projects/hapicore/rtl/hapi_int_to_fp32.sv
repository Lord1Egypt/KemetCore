// HapiCore — int32 -> fp32 convert (fcvt.s.w / fcvt.s.wu) — KemetCore Phase 2 RTL
//
// Scalar RISC-V F-extension integer-to-float convert, round-to-nearest-even.
// `is_signed` selects fcvt.s.w (two's-complement) vs fcvt.s.wu (unsigned). Take
// the magnitude, find its MSB, keep 24 significant bits and RNE-round the rest
// (a rounding carry may bump the exponent). A 32-bit integer always fits fp32's
// 8-bit exponent, so no overflow to Inf is possible.
//
// Verified bit-exact vs golden int_to_fp32 (== AtumCore _i2f) — see
// tb/test_int_to_fp32.py. Combinational.

module hapi_int_to_fp32 (
    input  logic [31:0] x,
    input  logic        is_signed,
    output logic [31:0] y
);
    wire        sign = is_signed & x[31];
    wire [31:0] mag  = sign ? (~x + 32'd1) : x;   // |x| (0x80000000 -> 2^31)

    // MSB index of mag (0..31); position of the leading 1
    logic [4:0] msb;
    integer k;
    always_comb begin
        msb = 5'd0;
        for (k = 0; k < 32; k++)
            if (mag[k]) msb = k[4:0];
    end

    logic [22:0] frac;
    logic [7:0]  exp;
    logic [4:0]  sh;
    logic [24:0] keep;            // 25 bits to catch a rounding carry-out
    logic        round_bit, sticky;
    logic [31:0] lsh, shr;
    always_comb begin
        // defaults so every signal is assigned on all paths (no latch)
        sh        = 5'd0;
        keep      = 25'd0;
        round_bit = 1'b0;
        sticky    = 1'b0;
        shr       = 32'd0;
        lsh       = (msb <= 5'd23) ? (mag << (5'd23 - msb)) : 32'd0;
        if (msb <= 5'd23) begin
            frac = lsh[22:0];                              // exact: fits in 23 bits
            exp  = {3'b0, msb};
        end else begin
            sh        = msb - 5'd23;                       // 1..8
            shr       = mag >> sh;                         // 24-bit significand
            keep      = {1'b0, shr[23:0]};
            round_bit = mag[sh - 5'd1];
            sticky    = |(mag & ((32'd1 << (sh - 5'd1)) - 32'd1));
            if (round_bit & (sticky | keep[0])) keep = keep + 25'd1;
            if (keep[24]) begin                            // carry-out -> renormalise
                keep = keep >> 1;
                exp  = {3'b0, msb} + 8'd1;
            end else begin
                exp  = {3'b0, msb};
            end
            frac = keep[22:0];
        end
    end

    assign y = (mag == 32'd0) ? 32'd0 : {sign, (exp + 8'd127), frac};
endmodule
