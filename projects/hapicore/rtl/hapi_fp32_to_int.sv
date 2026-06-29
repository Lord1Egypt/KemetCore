// HapiCore — fp32 -> int32 convert (fcvt.w.s / .wu.s / .rtz variants) — Phase 2 RTL
//
// Scalar RISC-V F-extension float-to-integer convert with RVV-style saturation.
// is_signed selects signed (fcvt.w.s) vs unsigned (fcvt.wu.s); truncate selects
// round-toward-zero (.rtz) vs round-to-nearest-even. Out-of-range / NaN saturate:
// NaN -> max representable; +Inf / too-large -> max; -Inf / too-small -> min
// (0 for unsigned); any negative -> 0 for unsigned.
//
// Algorithm (integer, no rational arithmetic): magnitude = full * 2^(e-23) where
// full is the 24-bit significand and e the unbiased exponent. A non-negative
// shift (e>=23) scales up — >=2^32 saturates; a negative shift scales down with
// guard/round/sticky for RNE. Then sign + range saturation. Verified bit-exact vs
// golden fp32_to_int (== AtumCore _f2i) — see tb/test_fp32_to_int.py. Combinational.

module hapi_fp32_to_int (
    input  logic [31:0] a,
    input  logic        is_signed,
    input  logic        truncate,
    output logic [31:0] y
);
    wire        sign = a[31];
    wire [7:0]  exp  = a[30:23];
    wire [22:0] mant = a[22:0];
    wire        is_inf = (exp == 8'hFF) && (mant == 23'd0);
    wire        is_nan = (exp == 8'hFF) && (mant != 23'd0);

    wire [31:0] posmax = is_signed ? 32'h7FFF_FFFF : 32'hFFFF_FFFF;
    wire [31:0] negmax = is_signed ? 32'h8000_0000 : 32'h0000_0000;

    wire [23:0] full = (exp == 8'd0) ? {1'b0, mant} : {1'b1, mant};
    wire signed [9:0] e  = (exp == 8'd0) ? -10'sd126 : ($signed({2'b0, exp}) - 10'sd127);
    wire signed [9:0] sh = e - 10'sd23;            // -149 .. 104

    // magnitude as a 33-bit value (enough to detect 2^32 overflow); plus an
    // explicit overflow flag for shifts that exceed 33 bits.
    logic [32:0] m;
    logic        ov;
    logic [9:0]  rsh;
    logic        rbit, sticky, roundup;
    always_comb begin
        m = 33'd0; ov = 1'b0; rsh = 10'd0; rbit = 1'b0; sticky = 1'b0; roundup = 1'b0;
        if (sh >= 10'sd0) begin
            if (sh >= 10'sd9) ov = 1'b1;                       // full<<sh >= 2^32
            else              m  = {9'd0, full} << sh[3:0];    // sh in 0..8
        end else begin
            rsh = 10'(-sh);                                    // 1 .. 149
            if (rsh >= 10'd25) begin
                m = 33'd0;                                     // shifted entirely out
            end else begin
                m      = {9'd0, (full >> rsh[4:0])};
                rbit   = full[rsh[4:0] - 5'd1];
                sticky = |(full & (({23'd0, 1'b1} << (rsh[4:0] - 5'd1)) - 24'd1));
                roundup = (~truncate) & rbit & (sticky | m[0]);
                m = m + {32'd0, roundup};
            end
        end
    end

    wire over_s_pos = ov | (m > 33'h0_7FFF_FFFF);
    wire over_s_neg = ov | (m > 33'h0_8000_0000);
    wire over_u_pos = ov | (m > 33'h0_FFFF_FFFF);
    wire [31:0] neg_m = (~m[31:0]) + 32'd1;        // -m

    always_comb begin
        if (is_nan)        y = posmax;
        else if (is_inf)   y = sign ? negmax : posmax;
        else if (full == 24'd0) y = 32'd0;         // +/- 0
        else if (is_signed) begin
            if (!sign) y = over_s_pos ? posmax : m[31:0];
            else       y = over_s_neg ? negmax : neg_m;
        end else begin
            if (sign)  y = 32'd0;                  // negative -> unsigned 0
            else       y = over_u_pos ? posmax : m[31:0];
        end
    end
endmodule
