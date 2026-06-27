// HapiCore — parameterized IEEE-754 fused multiply-add core (KemetCore Phase 2)
//
// Single-cycle combinational FMA: y = round(a*b + c) with a SINGLE final rounding
// (a true fused unit). This is the format-generic version of the verified
// hapi_fp32_fma datapath: the exact SIG_W-bit*SIG_W-bit product and the SIG_W-bit
// addend are aligned by their true exponents into a W-bit window anchored at the
// larger operand's MSB — wide enough to hold the entire rounding-relevant range
// exactly (full product width + cancellation headroom + guard); bits that fall
// past the window (only when one operand is too small to reach the round bit) are
// OR-collected into one sticky, with a sticky-borrow on effective subtraction.
// One leading-one normalise (for-loop priority encoder) + round-to-nearest-even.
//
// Thin wrappers (hapi_bf16_fma, hapi_fp16_fma) set the format parameters. Each is
// bit-exact against the single-rounded golden fp_fma (exact rational a*b+c, one
// rounding). Yosys-portable: exact widths, no latches.

module hapi_fma_core #(
    parameter int EXP_W  = 8,           // exponent field width
    parameter int MANT_W = 23,          // mantissa field width
    parameter int BIAS   = 127,         // exponent bias
    parameter int W      = 128          // alignment window width
) (
    input  logic [EXP_W+MANT_W:0] a,    // {sign, exp[EXP_W], mant[MANT_W]}
    input  logic [EXP_W+MANT_W:0] b,
    input  logic [EXP_W+MANT_W:0] c,
    output logic [EXP_W+MANT_W:0] y
);
    localparam int TOTAL  = EXP_W + MANT_W + 1;
    localparam int SIG_W  = MANT_W + 1;         // significand incl. implicit bit
    localparam int PROD_W = 2 * SIG_W;          // exact product width
    localparam int IDXW   = $clog2(W + 1);      // bit-index width into the window

    // signed 14-bit exponent constants (range covers bf16/fp16/fp32)
    localparam logic signed [13:0] PEOFF  = 14'(PROD_W - 1);       // product MSB offset
    localparam logic signed [13:0] CEOFF  = 14'(MANT_W);          // addend  MSB offset
    localparam logic signed [13:0] BIAS_S = 14'(BIAS);
    localparam logic signed [13:0] EXOFF  = 14'(BIAS + MANT_W);   // normal: EX = exp-EXOFF
    localparam logic signed [13:0] EXSUB  = 14'(1 - BIAS - MANT_W); // subnormal bit0 exponent
    localparam logic signed [13:0] EXPMX  = 14'((1 << EXP_W) - 1); // all-ones exponent
    localparam logic signed [13:0] WM1    = 14'(W - 1);
    localparam logic        [13:0] PRODWU = 14'(PROD_W);
    localparam logic        [9:0]  WLIM   = 10'(W);
    localparam logic [EXP_W-1:0]   EALL   = '1;

    localparam logic [TOTAL-1:0] QNAN = {1'b0, EALL, 1'b1, {(MANT_W-1){1'b0}}};
    localparam logic [TOTAL-1:0] INF  = {1'b0, EALL, {MANT_W{1'b0}}};

    // ---- field extraction ------------------------------------------------- //
    logic              sa, sb, sc;
    logic [EXP_W-1:0]  ea, eb, ec;
    logic [MANT_W-1:0] ma, mb, mc;
    assign sa = a[TOTAL-1]; assign ea = a[TOTAL-2 -: EXP_W]; assign ma = a[MANT_W-1:0];
    assign sb = b[TOTAL-1]; assign eb = b[TOTAL-2 -: EXP_W]; assign mb = b[MANT_W-1:0];
    assign sc = c[TOTAL-1]; assign ec = c[TOTAL-2 -: EXP_W]; assign mc = c[MANT_W-1:0];

    logic a_zero, b_zero, c_zero, a_inf, b_inf, c_inf, a_nan, b_nan, c_nan;
    assign a_zero = (ea == '0) && (ma == '0);
    assign b_zero = (eb == '0) && (mb == '0);
    assign c_zero = (ec == '0) && (mc == '0);
    assign a_inf  = (ea == EALL) && (ma == '0);
    assign b_inf  = (eb == EALL) && (mb == '0);
    assign c_inf  = (ec == EALL) && (mc == '0);
    assign a_nan  = (ea == EALL) && (ma != '0);
    assign b_nan  = (eb == EALL) && (mb != '0);
    assign c_nan  = (ec == EALL) && (mc != '0);

    // integer significand and bit0-exponent (signed) per operand: x = SX * 2**EX
    logic [SIG_W-1:0]   siga, sigb, sigc;
    assign siga = (ea == '0) ? {1'b0, ma} : {1'b1, ma};
    assign sigb = (eb == '0) ? {1'b0, mb} : {1'b1, mb};
    assign sigc = (ec == '0) ? {1'b0, mc} : {1'b1, mc};
    logic signed [13:0] exa, exb, exc;
    assign exa = (ea == '0) ? EXSUB : ($signed({{(14-EXP_W){1'b0}}, ea}) - EXOFF);
    assign exb = (eb == '0) ? EXSUB : ($signed({{(14-EXP_W){1'b0}}, eb}) - EXOFF);
    assign exc = (ec == '0) ? EXSUB : ($signed({{(14-EXP_W){1'b0}}, ec}) - EXOFF);

    // ---- exact product + window anchor ------------------------------------ //
    logic [PROD_W-1:0]  sigp;
    logic               sp;
    logic signed [13:0] exp_p, pe, ce, eff_pe, eff_ce, topmax, wbot, off_p, off_c;
    assign sigp   = siga * sigb;
    assign sp     = sa ^ sb;
    assign exp_p  = exa + exb;
    assign pe     = exp_p + PEOFF;
    assign ce     = exc + CEOFF;
    assign eff_pe = (a_zero || b_zero) ? -14'sd4096 : pe;
    assign eff_ce = c_zero             ? -14'sd4096 : ce;
    assign topmax = ((eff_pe >= eff_ce) ? eff_pe : eff_ce) + 14'sd2;
    assign wbot   = topmax - WM1;
    assign off_p  = exp_p - wbot;
    assign off_c  = exc   - wbot;

    // place a significand into the window; bits below the window OR into sticky
    function automatic logic [W-1:0] place(input logic [PROD_W-1:0] sig,
                                           input logic signed [13:0] off,
                                           output logic stk);
        logic [13:0]        r;
        logic [PROD_W-1:0]  lowmask;
        begin
            if (off >= 0) begin
                place = {{(W-PROD_W){1'b0}}, sig} << off[9:0];
                stk   = 1'b0;
            end else begin
                r = -off;
                if (r >= PRODWU) begin
                    place = '0;
                    stk   = |sig;
                end else begin
                    place   = {{(W-PROD_W){1'b0}}, (sig >> r[9:0])};
                    lowmask = (({{(PROD_W-1){1'b0}}, 1'b1}) << r[9:0]) - {{(PROD_W-1){1'b0}}, 1'b1};
                    stk     = |(sig & lowmask);
                end
            end
        end
    endfunction

    logic [W-1:0] field_p, field_c;
    logic         stk_p, stk_c;
    assign field_p = place(sigp, off_p, stk_p);
    assign field_c = place({{(PROD_W-SIG_W){1'b0}}, sigc}, off_c, stk_c);

    // ---- signed combine into magnitude + sign ----------------------------- //
    logic [W:0] mag;
    logic       rsign, stk_lo;
    logic       p_ge_c;
    assign p_ge_c = (field_p >= field_c);
    assign stk_lo = stk_p | stk_c;
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
    function automatic logic [9:0] msb_index(input logic [W:0] x);
        integer i;
        logic   found;
        begin
            msb_index = 10'd0;
            found     = 1'b0;
            for (i = W; i >= 0; i = i - 1)
                if (!found && x[i]) begin
                    msb_index = i[9:0];
                    found     = 1'b1;
                end
        end
    endfunction

    logic [9:0]         kidx;
    logic signed [13:0] ebias_norm, rs_s;
    logic               is_norm;
    logic [9:0]         rs, gpos;
    assign kidx       = msb_index(mag);
    assign ebias_norm = wbot + $signed({4'b0, kidx}) + BIAS_S;
    assign is_norm    = (ebias_norm >= 14'sd1);
    assign rs_s       = is_norm ? ($signed({4'b0, kidx}) - CEOFF) : (EXSUB - wbot);
    assign rs         = rs_s[9:0];
    assign gpos       = rs - 10'd1;

    // ---- single round-to-nearest-even ------------------------------------- //
    logic [TOTAL-1:0] arith_bits;
    always_comb begin
        logic [W:0]         shifted, gmask;
        logic [SIG_W-1:0]   keep;
        logic               guard, rest, round_up;
        logic [SIG_W:0]     rounded;
        logic signed [13:0] bexp;
        logic [EXP_W-1:0]   expfield;

        shifted    = mag >> rs;
        keep       = shifted[SIG_W-1:0];
        guard      = (gpos <= WLIM) ? mag[gpos[IDXW-1:0]] : 1'b0;
        gmask      = (({{W{1'b0}}, 1'b1}) << gpos) - {{W{1'b0}}, 1'b1};
        rest       = (|(mag & gmask)) | stk_lo;
        round_up   = guard & (rest | keep[0]);
        rounded    = {1'b0, keep} + {{SIG_W{1'b0}}, round_up};
        bexp       = ebias_norm + {13'b0, rounded[SIG_W]};
        expfield   = rounded[SIG_W-1] ? {{(EXP_W-1){1'b0}}, 1'b1} : '0;
        arith_bits = '0;

        if (mag == {(W+1){1'b0}}) begin
            arith_bits = '0;
        end else if (is_norm) begin
            if (bexp >= EXPMX)
                arith_bits = {rsign, INF[TOTAL-2:0]};        // overflow -> Inf
            else
                arith_bits = {rsign, bexp[EXP_W-1:0], rounded[MANT_W-1:0]};
        end else begin
            arith_bits = {rsign, expfield, rounded[MANT_W-1:0]};
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    logic prod_inf, prod_invalid;
    assign prod_invalid = (a_inf && b_zero) || (b_inf && a_zero);
    assign prod_inf     = (a_inf && !b_zero) || (b_inf && !a_zero);

    always_comb begin
        if (a_nan || b_nan || c_nan || prod_invalid)
            y = QNAN;
        else if (prod_inf && c_inf && (sp != sc))
            y = QNAN;
        else if (prod_inf)
            y = {sp, INF[TOTAL-2:0]};
        else if (c_inf)
            y = {sc, INF[TOTAL-2:0]};
        else if (mag == {(W+1){1'b0}})
            y = stk_lo ? {rsign, {(TOTAL-1){1'b0}}}
              : (((a_zero || b_zero) && c_zero && sp && sc) ? {1'b1, {(TOTAL-1){1'b0}}}
                                                            : {TOTAL{1'b0}});
        else
            y = arith_bits;
    end
endmodule


// ---- format wrappers ------------------------------------------------------ //
module hapi_bf16_fma (input logic [15:0] a, b, c, output logic [15:0] y);
    hapi_fma_core #(.EXP_W(8), .MANT_W(7), .BIAS(127), .W(48))
        u (.a(a), .b(b), .c(c), .y(y));
endmodule

module hapi_fp16_fma (input logic [15:0] a, b, c, output logic [15:0] y);
    hapi_fma_core #(.EXP_W(5), .MANT_W(10), .BIAS(15), .W(48))
        u (.a(a), .b(b), .c(c), .y(y));
endmodule
