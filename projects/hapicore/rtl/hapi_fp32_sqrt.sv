// HapiCore — fp32 square root (KemetCore Phase 2 RTL)
//
// Single-cycle combinational IEEE-754 binary32 sqrt: y = round(sqrt(x)),
// correctly rounded. Every fp32 sqrt result is a NORMAL number (sqrt of the
// smallest subnormal ~2**-74.5 is far above the min normal, sqrt of the max
// ~2**64), so there is no subnormal/overflow/underflow handling.
//
// Strategy: normalise x to M * 2**G with M in [2**23, 2**24) (subnormals via a
// 24-bit CLZ). sqrt(x) = sqrt(F) * 2**floor(G/2) where F = M (G even) or 2*M
// (G odd) makes the exponent even. Then one exact integer square root of
// (F << 28) yields 24 significand bits + guard, and the sqrt REMAINDER provides
// an exact sticky bit. Round-to-nearest-even; the result MSB is at bit 25 or 26
// of the root (no priority encoder needed).
//
// fp32 layout: [31] sign | [30:23] exponent (bias 127) | [22:0] mantissa.
// Bit-exact against golden.fp_sqrt (exact integer-sqrt intermediate) — see
// tb/test_fp32_sqrt.py. Yosys-portable (unrolled digit-recurrence), no latches.

module hapi_fp32_sqrt (
    input  logic [31:0] x,
    output logic [31:0] y
);
    localparam logic [31:0] QNAN = 32'h7FC00000;
    localparam logic [31:0] INF  = 32'h7F800000;

    logic        sx;
    logic [7:0]  ex;
    logic [22:0] mx;
    assign sx = x[31]; assign ex = x[30:23]; assign mx = x[22:0];

    logic x_zero, x_inf, x_nan;
    assign x_zero = (ex == 8'h00) && (mx == 23'h0);
    assign x_inf  = (ex == 8'hFF) && (mx == 23'h0);
    assign x_nan  = (ex == 8'hFF) && (mx != 23'h0);

    // count leading zeros of a 24-bit value (1..24; normalises subnormals)
    function automatic logic [4:0] clz24(input logic [23:0] v);
        logic [4:0] n; logic found; integer i;
        begin
            n = 5'd24; found = 1'b0;
            for (i = 23; i >= 0; i = i - 1)
                if (!found && v[i]) begin n = 5'd23 - i[4:0]; found = 1'b1; end
            clz24 = n;
        end
    endfunction

    // ---- normalise: x = M * 2**G, M in [2**23, 2**24) --------------------- //
    logic [23:0]        m_pk, m;
    logic [4:0]         shx;
    logic signed [13:0] g;
    assign m_pk = (ex == 8'h00) ? {1'b0, mx} : {1'b1, mx};
    assign shx  = (ex == 8'h00) ? clz24(m_pk) : 5'd0;
    assign m    = m_pk << shx;
    assign g    = (ex == 8'h00) ? (-14'sd149 - $signed({9'b0, shx})) : ($signed({6'b0, ex}) - 14'sd150);

    // radicand F = M (G even) or 2*M (G odd); RAD = F << 28 (<= 53 bits)
    logic [24:0] f;
    logic [53:0] rad;
    assign f   = g[0] ? {m, 1'b0} : {1'b0, m};
    assign rad = {1'b0, f, 28'b0};

    // ---- exact integer square root: Q = isqrt(RAD), rem = RAD - Q*Q -------- //
    function automatic logic [26:0] isqrt54(input logic [53:0] radi, output logic [54:0] remo);
        logic [54:0] rem; logic [26:0] root; logic [54:0] tst; integer i;
        begin
            rem = 55'b0; root = 27'b0;
            for (i = 26; i >= 0; i = i - 1) begin
                rem = (rem << 2) | {53'b0, radi[2*i +: 2]};
                tst = {26'b0, root, 2'b01};            // (root << 2) | 1
                if (rem >= tst) begin
                    rem  = rem - tst;
                    root = (root << 1) | 27'b1;
                end else begin
                    root = root << 1;
                end
            end
            remo = rem; isqrt54 = root;
        end
    endfunction

    logic [26:0] qroot;
    logic [54:0] qrem;
    logic        rem_nz;
    assign qroot  = isqrt54(rad, qrem);
    assign rem_nz = |qrem;

    // ---- magnitude round (result is always normal) ------------------------ //
    logic [7:0]         kidx;
    logic signed [13:0] wbot, biased_norm;
    logic [4:0]         rs, gpos;
    assign kidx        = qroot[26] ? 8'd26 : 8'd25;          // Q in [2**25, 2**26.5)
    assign wbot        = (g >>> 1) - 14'sd14;                // floor(G/2) - 14
    assign biased_norm = $signed({6'b0, kidx}) + wbot + 14'sd127;
    assign rs          = kidx[4:0] - 5'd23;                  // 2 or 3
    assign gpos        = rs - 5'd1;

    logic [31:0] arith_bits;
    always_comb begin
        logic [26:0] keep_sh, lowmask;
        logic [23:0] keep;
        logic        guard, rest, round_up;
        logic [24:0] rounded;
        logic signed [13:0] bexp;

        keep_sh = qroot >> rs;
        keep    = keep_sh[23:0];
        guard   = qroot[gpos];
        lowmask = (27'b1 << gpos) - 27'b1;
        rest    = (|(qroot & lowmask)) | rem_nz;
        round_up = guard & (rest | keep[0]);
        rounded  = {1'b0, keep} + {24'b0, round_up};
        bexp     = biased_norm + {13'b0, rounded[24]};       // round carry -> exp++
        arith_bits = {1'b0, bexp[7:0], rounded[22:0]};       // sqrt result is positive
    end

    // ---- top-level special-case mux --------------------------------------- //
    always_comb begin
        if (x_nan)
            y = QNAN;
        else if (sx && !x_zero)
            y = QNAN;                                // sqrt of a negative (incl -Inf)
        else if (x_zero)
            y = {sx, 31'b0};                         // sqrt(+0)=+0, sqrt(-0)=-0
        else if (x_inf)
            y = INF;                                 // sqrt(+Inf) = +Inf
        else
            y = arith_bits;
    end
endmodule
