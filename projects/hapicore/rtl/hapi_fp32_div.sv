// HapiCore — fp32 divide (KemetCore Phase 2 RTL)
//
// Single-cycle combinational IEEE-754 binary32 divide: y = round(a / b) with a
// SINGLE correctly-rounded result. Strategy: normalise both significands to
// [2**23, 2**24) (tracking each operand's bit0 exponent), then form the quotient
// by one exact integer division of a 51-bit dividend (Sa << 27) by the 24-bit
// divisor — the quotient gives 24 significand bits + guard, and the division
// REMAINDER provides an exact sticky bit (rem != 0 => the true quotient has more
// below). The normalise-and-round tail is the same magnitude-rounding the FMA
// uses: leading-one position -> biased exponent, round-to-nearest-even, subnormal
// (gradual underflow) via a clamped right shift, overflow -> Inf.
//
//   q = Sa/Sb in (0.5, 2) since both are in [2**23, 2**24), so the quotient MSB is
//   at bit 27 (q>=1) or 26 (q<1) — no full priority encoder needed.
//
// fp32 layout: [31] sign | [30:23] exponent (bias 127) | [22:0] mantissa.
// Bit-exact against golden.fp_div (exact rational a/b, one rounding) — see
// tb/test_fp32_div.py. Yosys-portable (uses $div/$mod), no latches.

module hapi_fp32_div (
    input  logic [31:0] a,
    input  logic [31:0] b,
    output logic [31:0] y
);
    localparam logic [31:0] QNAN = 32'h7FC00000;
    localparam logic [31:0] INF  = 32'h7F800000;

    // ---- field extraction ------------------------------------------------- //
    logic        sa, sb;
    logic [7:0]  ea, eb;
    logic [22:0] ma, mb;
    assign sa = a[31]; assign ea = a[30:23]; assign ma = a[22:0];
    assign sb = b[31]; assign eb = b[30:23]; assign mb = b[22:0];

    logic a_zero, b_zero, a_inf, b_inf, a_nan, b_nan;
    assign a_zero = (ea == 8'h00) && (ma == 23'h0);
    assign b_zero = (eb == 8'h00) && (mb == 23'h0);
    assign a_inf  = (ea == 8'hFF) && (ma == 23'h0);
    assign b_inf  = (eb == 8'hFF) && (mb == 23'h0);
    assign a_nan  = (ea == 8'hFF) && (ma != 23'h0);
    assign b_nan  = (eb == 8'hFF) && (mb != 23'h0);

    logic sign;
    assign sign = sa ^ sb;

    // count leading zeros of a 24-bit value (1..24; used to normalise subnormals)
    function automatic logic [4:0] clz24(input logic [23:0] x);
        logic [4:0] n; logic found; integer i;
        begin
            n = 5'd24; found = 1'b0;
            for (i = 23; i >= 0; i = i - 1)
                if (!found && x[i]) begin n = 5'd23 - i[4:0]; found = 1'b1; end
            clz24 = n;
        end
    endfunction

    // ---- normalise each operand to Sn in [2**23, 2**24), value = Sn * 2**Gx -- //
    logic [23:0]        ma_pk, mb_pk, sna, snb;
    logic [4:0]         sha, shb;
    logic signed [13:0] ga, gb;
    assign ma_pk = (ea == 8'h00) ? {1'b0, ma} : {1'b1, ma};
    assign mb_pk = (eb == 8'h00) ? {1'b0, mb} : {1'b1, mb};
    assign sha   = (ea == 8'h00) ? clz24(ma_pk) : 5'd0;
    assign shb   = (eb == 8'h00) ? clz24(mb_pk) : 5'd0;
    assign sna   = ma_pk << sha;
    assign snb   = mb_pk << shb;
    assign ga    = (ea == 8'h00) ? (-14'sd149 - $signed({9'b0, sha})) : ($signed({6'b0, ea}) - 14'sd150);
    assign gb    = (eb == 8'h00) ? (-14'sd149 - $signed({9'b0, shb})) : ($signed({6'b0, eb}) - 14'sd150);

    // ---- exact quotient + remainder sticky -------------------------------- //
    logic [50:0] dividend, qfull, remfull;
    logic [27:0] qint;
    logic [23:0] rem;
    logic        rem_nz;
    assign dividend = {27'b0, sna} << 27;          // Sa * 2**27 (51-bit)
    assign qfull    = dividend / {27'b0, snb};     // q * 2**27, in [2**26, 2**28)
    assign remfull  = dividend % {27'b0, snb};     // 0 <= rem < Snb (< 2**24)
    assign qint     = qfull[27:0];
    assign rem      = remfull[23:0];
    assign rem_nz   = |rem;

    // quotient MSB is bit 27 (q>=1) or bit 26 (q<1)
    logic [7:0]         kidx;
    logic signed [13:0] wbot, ebias_norm, rs_s;
    logic               is_norm;
    logic [8:0]         rs, gpos;
    assign kidx       = qint[27] ? 8'd27 : 8'd26;
    assign wbot       = ga - gb - 14'sd27;          // exponent of qint bit0
    assign ebias_norm = wbot + $signed({6'b0, kidx}) + 14'sd127;
    assign is_norm    = (ebias_norm >= 14'sd1);
    assign rs_s       = is_norm ? ($signed({6'b0, kidx}) - 14'sd23) : (-14'sd149 - wbot);
    assign rs         = rs_s[8:0];
    assign gpos       = rs - 9'd1;

    // ---- single round-to-nearest-even ------------------------------------- //
    logic [31:0] arith_bits;
    always_comb begin
        logic [27:0] shifted, gmask;
        logic [23:0] keep;
        logic        guard, rest, round_up;
        logic [24:0] rounded;
        logic signed [13:0] bexp;
        logic [7:0]  expfield;

        shifted    = qint >> rs;
        keep       = shifted[23:0];
        guard      = (gpos <= 9'd27) ? qint[gpos[4:0]] : 1'b0;
        gmask      = (28'b1 << gpos) - 28'b1;
        rest       = (|(qint & gmask)) | rem_nz;
        round_up   = guard & (rest | keep[0]);
        rounded    = {1'b0, keep} + {24'b0, round_up};
        bexp       = ebias_norm + {13'b0, rounded[24]};
        expfield   = rounded[23] ? 8'd1 : 8'd0;
        arith_bits = 32'h0000_0000;

        if (is_norm) begin
            if (bexp >= 14'sd255)
                arith_bits = {sign, INF[30:0]};              // overflow -> Inf
            else
                arith_bits = {sign, bexp[7:0], rounded[22:0]};
        end else begin
            arith_bits = {sign, expfield, rounded[22:0]};    // subnormal / underflow
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    always_comb begin
        if (a_nan || b_nan)
            y = QNAN;
        else if (a_inf && b_inf)
            y = QNAN;                               // Inf / Inf
        else if (b_zero)
            y = a_zero ? QNAN : {sign, INF[30:0]};  // 0/0 -> NaN ; x/0 -> Inf
        else if (a_inf)
            y = {sign, INF[30:0]};
        else if (b_inf || a_zero)
            y = {sign, 31'b0};                       // finite/Inf or 0/finite -> signed 0
        else
            y = arith_bits;
    end
endmodule
