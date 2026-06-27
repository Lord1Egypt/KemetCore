// HapiCore — fp32 fused multiply-add (KemetCore Phase 2 RTL)
//
// Single-cycle combinational IEEE-754 binary32 FMA: y = round(a*b + c) with a
// SINGLE final rounding (a true fused unit, not mul-then-add). This is the
// headline ML primitive — every BastCore/GebCore MAC is conceptually an FMA.
//
// Strategy: a bounded alignment WINDOW with a sticky tail. The product a*b is
// exact (48-bit significand) and the addend c is exact (24-bit). Both are placed
// by their true exponents into a 128-bit window anchored at the larger operand's
// MSB; the window is wide enough to hold the entire rounding-relevant range
// EXACTLY (full product width + cancellation headroom + guard), and any bits
// that fall below the window — which only happens when one operand is so much
// smaller it cannot reach the round bit — are OR-collected into a single sticky.
// So |a*b + c| is represented with the precision rounding needs and one
// round-to-nearest-even is applied. This is the classic single-path FMA; it is
// bit-exact against the single-rounded golden (which rounds the exact rational
// a*b+c once), and far smaller than a full-range exact lane.
//
//   Why 128 bits suffice: heavy cancellation only occurs for comparable-magnitude
//   operands, whose significant bits then all sit inside the window (sticky=0, so
//   the result is exact); when operands differ enough to push bits past the
//   window bottom, one dominates and those bits are correctly sticky-only.
//
// fp32 layout: [31] sign | [30:23] exponent (bias 127) | [22:0] mantissa.
// See tb/test_fp32_fma.py. Yosys-portable: exact widths, for-loop priority
// encoder, no latches.

module hapi_fp32_fma (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    output logic [31:0] y
);
    localparam int W = 128;             // alignment window width
    localparam logic [31:0] QNAN = 32'h7FC00000;
    localparam logic [31:0] INF  = 32'h7F800000;

    // ---- field extraction ------------------------------------------------- //
    logic        sa, sb, sc;
    logic [7:0]  ea, eb, ec;
    logic [22:0] ma, mb, mc;
    assign sa = a[31]; assign ea = a[30:23]; assign ma = a[22:0];
    assign sb = b[31]; assign eb = b[30:23]; assign mb = b[22:0];
    assign sc = c[31]; assign ec = c[30:23]; assign mc = c[22:0];

    logic a_zero, b_zero, c_zero, a_inf, b_inf, c_inf, a_nan, b_nan, c_nan;
    assign a_zero = (ea == 8'h00) && (ma == 23'h0);
    assign b_zero = (eb == 8'h00) && (mb == 23'h0);
    assign c_zero = (ec == 8'h00) && (mc == 23'h0);
    assign a_inf  = (ea == 8'hFF) && (ma == 23'h0);
    assign b_inf  = (eb == 8'hFF) && (mb == 23'h0);
    assign c_inf  = (ec == 8'hFF) && (mc == 23'h0);
    assign a_nan  = (ea == 8'hFF) && (ma != 23'h0);
    assign b_nan  = (eb == 8'hFF) && (mb != 23'h0);
    assign c_nan  = (ec == 8'hFF) && (mc != 23'h0);

    // integer significand and bit0-exponent (signed) per operand: x = SX * 2**EX
    logic [23:0] siga, sigb, sigc;
    assign siga = (ea == 8'h00) ? {1'b0, ma} : {1'b1, ma};
    assign sigb = (eb == 8'h00) ? {1'b0, mb} : {1'b1, mb};
    assign sigc = (ec == 8'h00) ? {1'b0, mc} : {1'b1, mc};
    logic signed [13:0] exa, exb, exc;  // [-149, 104]
    assign exa = (ea == 8'h00) ? -14'sd149 : ($signed({6'b0, ea}) - 14'sd150);
    assign exb = (eb == 8'h00) ? -14'sd149 : ($signed({6'b0, eb}) - 14'sd150);
    assign exc = (ec == 8'h00) ? -14'sd149 : ($signed({6'b0, ec}) - 14'sd150);

    // ---- exact product + window anchor ------------------------------------ //
    logic [47:0]        sigp;           // SA*SB exact 48-bit
    logic               sp;
    logic signed [13:0] exp_p, pe, ce, eff_pe, eff_ce, topmax, wbot, off_p, off_c;
    assign sigp   = siga * sigb;
    assign sp     = sa ^ sb;
    assign exp_p  = exa + exb;          // EP
    assign pe     = exp_p + 14'sd47;    // product nominal MSB exponent
    assign ce     = exc + 14'sd23;      // addend nominal MSB exponent
    // anchor the window at the larger NON-ZERO operand (a zero operand carries a
    // meaningless exponent and must not pull the anchor)
    assign eff_pe = (a_zero || b_zero) ? -14'sd4096 : pe;
    assign eff_ce = c_zero             ? -14'sd4096 : ce;
    assign topmax = ((eff_pe >= eff_ce) ? eff_pe : eff_ce) + 14'sd2;  // 2b carry headroom
    assign wbot   = topmax - 14'sd127;  // exponent of window bit 0
    assign off_p  = exp_p - wbot;       // product bit0 position in window (signed)
    assign off_c  = exc   - wbot;       // addend  bit0 position in window (signed)

    // place a significand into the window; bits below the window OR into sticky
    function automatic logic [W-1:0] place(input logic [47:0] sig,
                                           input int unsigned width,
                                           input logic signed [13:0] off,
                                           output logic stk);
        logic [13:0] r;
        logic [47:0] lost;
        begin
            if (off >= 0) begin
                place = {{(W-48){1'b0}}, sig} << off[7:0];   // larger operand fits
                stk   = 1'b0;
            end else begin
                r = -off;
                if (r >= 14'sd48) begin
                    place = '0;
                    stk   = |sig;
                end else begin
                    place = {{(W-48){1'b0}}, (sig >> r[5:0])};
                    lost  = sig & ((48'b1 << r[5:0]) - 48'b1);
                    stk   = |lost;
                end
            end
        end
    endfunction

    logic [W-1:0] field_p, field_c;
    logic         stk_p, stk_c;
    assign field_p = place(sigp,          48, off_p, stk_p);
    assign field_c = place({24'b0, sigc}, 24, off_c, stk_c);

    // ---- signed combine into magnitude + sign ----------------------------- //
    logic [W:0] mag;                    // W+1 bits for add carry
    logic       rsign, stk_lo;
    logic       p_ge_c;
    assign p_ge_c = (field_p >= field_c);
    assign stk_lo = stk_p | stk_c;      // far-tail bits (only the smaller drops any)
    // On effective subtraction, the subtrahend's dropped tail (stk_lo; the minuend
    // never drops bits) makes the true value 1 window-LSB smaller -> borrow it in,
    // keeping stk_lo=1 as sticky. Addition needs no borrow (the tail only adds).
    always_comb begin
        if (sp == sc) begin
            mag   = {1'b0, field_p} + {1'b0, field_c};
            rsign = sp;
        end else if (p_ge_c) begin
            mag   = {1'b0, field_p} - {1'b0, field_c} - {{W{1'b0}}, stk_lo};
            rsign = sp;
        end else begin
            mag   = {1'b0, field_c} - {1'b0, field_p} - {{W{1'b0}}, stk_lo};
            rsign = sc;
        end
    end

    // ---- leading-one index of the magnitude ------------------------------- //
    function automatic logic [7:0] msb_index(input logic [W:0] x);
        integer i;
        logic   found;
        begin
            msb_index = 8'd0;
            found     = 1'b0;
            for (i = W; i >= 0; i = i - 1)
                if (!found && x[i]) begin
                    msb_index = i[7:0];
                    found     = 1'b1;
                end
        end
    endfunction

    logic [7:0]         kidx;
    logic signed [13:0] ebias_norm;     // biased exp assuming leading 1
    logic               is_norm;
    logic signed [13:0] rs_s;           // result-LSB index into mag (signed)
    logic [8:0]         rs, gpos;       // may exceed W when the value underflows far below
    assign kidx       = msb_index(mag);
    assign ebias_norm = wbot + $signed({6'b0, kidx}) + 14'sd127;
    assign is_norm    = (ebias_norm >= 14'sd1);
    assign rs_s       = is_norm ? ($signed({6'b0, kidx}) - 14'sd23) : (-14'sd149 - wbot);
    assign rs         = rs_s[8:0];
    assign gpos       = rs - 9'd1;

    // ---- single round-to-nearest-even ------------------------------------- //
    logic [31:0] arith_bits;
    always_comb begin
        logic [W:0] shifted, gmask;
        logic [23:0] keep;
        logic        guard, rest, round_up;
        logic [24:0] rounded;
        logic signed [13:0] bexp;
        logic [7:0]  expfield;

        shifted    = mag >> rs;                    // rs may exceed W -> 0 (value underflows)
        keep       = shifted[23:0];
        guard      = (gpos <= 9'd128) ? mag[gpos[7:0]] : 1'b0;
        gmask      = (({{W{1'b0}}, 1'b1}) << gpos) - {{W{1'b0}}, 1'b1};  // gpos>W -> all ones
        rest       = (|(mag & gmask)) | stk_lo;    // everything strictly below guard
        round_up   = guard & (rest | keep[0]);
        rounded    = {1'b0, keep} + {24'b0, round_up};
        bexp       = ebias_norm + {13'b0, rounded[24]};   // carry 0xFFFFFF+1 -> exp++
        expfield   = rounded[23] ? 8'd1 : 8'd0;
        arith_bits = 32'h0000_0000;

        if (mag == {(W+1){1'b0}}) begin
            arith_bits = 32'h0000_0000;            // exact zero -> +0
        end else if (is_norm) begin
            if (bexp >= 14'sd255)
                arith_bits = {rsign, INF[30:0]};         // overflow -> Inf
            else
                arith_bits = {rsign, bexp[7:0], rounded[22:0]};
        end else begin
            arith_bits = {rsign, expfield, rounded[22:0]};  // subnormal (may promote)
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    logic prod_inf, prod_invalid;
    assign prod_invalid = (a_inf && b_zero) || (b_inf && a_zero);   // 0 * Inf
    assign prod_inf     = (a_inf && !b_zero) || (b_inf && !a_zero);

    always_comb begin
        if (a_nan || b_nan || c_nan || prod_invalid)
            y = QNAN;
        else if (prod_inf && c_inf && (sp != sc))
            y = QNAN;                               // Inf + (-Inf)
        else if (prod_inf)
            y = {sp, INF[30:0]};
        else if (c_inf)
            y = {sc, INF[30:0]};
        else if (mag == {(W+1){1'b0}})
            // exact zero -> +0 (or -0 for -0 + -0); a sub-window tail -> signed zero
            y = stk_lo ? {rsign, 31'b0}
              : (((a_zero || b_zero) && c_zero && sp && sc) ? 32'h8000_0000 : 32'h0000_0000);
        else
            y = arith_bits;
    end
endmodule
