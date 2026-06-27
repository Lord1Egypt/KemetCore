// HapiCore — fp16 (IEEE-754 half) multiplier (KemetCore Phase 2 RTL)
//
// Single-cycle combinational binary16 multiply with full IEEE-754 handling:
//   * sign = sign_a ^ sign_b
//   * NaN propagation, Inf*0 -> NaN, Inf*finite -> Inf, x*0 -> 0
//   * subnormal INPUTS (exp==0) treated with their true value (no flush-to-zero)
//   * round-to-nearest-ties-to-even on the exact 22-bit product
//   * overflow -> Inf, underflow -> subnormal/zero (with correct RNE)
//
// fp16 layout: [15] sign | [14:10] exponent (bias 15) | [9:0] mantissa.
// This is the bf16 multiplier widened to fp16's field sizes: 11-bit significands,
// a 22-bit product, and a biased result exponent of (expa + expb - 14 - lz).
// Bit-exact against the Python golden hapi_fpu.fp_mul(a, b, "fp16") (numpy
// float16) — see tb/test_fp16_mul.py.
//
// Yosys-portable: no int'() casts, exact-width function ports, rounding in
// module-level always_comb.

module hapi_fp16_mul (
    input  logic [15:0] a,
    input  logic [15:0] b,
    output logic [15:0] y
);
    // ---- field extraction ------------------------------------------------- //
    logic       sa, sb, sy;
    logic [4:0] ea, eb;
    logic [9:0] ma, mb;
    assign sa = a[15];  assign ea = a[14:10];  assign ma = a[9:0];
    assign sb = b[15];  assign eb = b[14:10];  assign mb = b[9:0];
    assign sy = sa ^ sb;

    // class flags
    logic a_zero, b_zero, a_inf, b_inf, a_nan, b_nan, a_sub, b_sub;
    assign a_zero = (ea == 5'h00) && (ma == 10'h000);
    assign b_zero = (eb == 5'h00) && (mb == 10'h000);
    assign a_sub  = (ea == 5'h00) && (ma != 10'h000);
    assign b_sub  = (eb == 5'h00) && (mb != 10'h000);
    assign a_inf  = (ea == 5'h1F) && (ma == 10'h000);
    assign b_inf  = (eb == 5'h1F) && (mb == 10'h000);
    assign a_nan  = (ea == 5'h1F) && (ma != 10'h000);
    assign b_nan  = (eb == 5'h1F) && (mb != 10'h000);

    localparam logic [15:0] QNAN = 16'h7E00;  // canonical quiet NaN (fp16)
    localparam logic [14:0] INF  = 15'h7C00;  // fp16 Inf without sign

    // ---- significands & effective exponents ------------------------------- //
    // 11-bit significand {implicit, mantissa}; subnormals use implicit 0, exp 1.
    logic [10:0] siga, sigb;
    logic [5:0]  expa, expb;
    assign siga = a_sub ? {1'b0, ma} : {1'b1, ma};
    assign sigb = b_sub ? {1'b0, mb} : {1'b1, mb};
    assign expa = a_sub ? 6'd1 : {1'b0, ea};
    assign expb = b_sub ? 6'd1 : {1'b0, eb};

    // exact 22-bit product of the two 11-bit significands
    logic [21:0] prod;
    assign prod = siga * sigb;

    // ---- leading-zero count of the 22-bit product ------------------------- //
    function automatic logic [4:0] clz22(input logic [21:0] x);
        casez (x)
            22'b1?????????????????????: clz22 = 5'd0;
            22'b01????????????????????: clz22 = 5'd1;
            22'b001???????????????????: clz22 = 5'd2;
            22'b0001??????????????????: clz22 = 5'd3;
            22'b00001?????????????????: clz22 = 5'd4;
            22'b000001????????????????: clz22 = 5'd5;
            22'b0000001???????????????: clz22 = 5'd6;
            22'b00000001??????????????: clz22 = 5'd7;
            22'b000000001?????????????: clz22 = 5'd8;
            22'b0000000001????????????: clz22 = 5'd9;
            22'b00000000001???????????: clz22 = 5'd10;
            22'b000000000001??????????: clz22 = 5'd11;
            22'b0000000000001?????????: clz22 = 5'd12;
            22'b00000000000001????????: clz22 = 5'd13;
            22'b000000000000001???????: clz22 = 5'd14;
            22'b0000000000000001??????: clz22 = 5'd15;
            22'b00000000000000001?????: clz22 = 5'd16;
            22'b000000000000000001????: clz22 = 5'd17;
            22'b0000000000000000001???: clz22 = 5'd18;
            22'b00000000000000000001??: clz22 = 5'd19;
            22'b000000000000000000001?: clz22 = 5'd20;
            22'b0000000000000000000001: clz22 = 5'd21;
            default:                    clz22 = 5'd22;  // x==0 (not reached here)
        endcase
    endfunction

    logic [4:0]  lz;
    logic [21:0] norm;          // product left-normalised so bit21 = leading 1
    assign lz   = clz22(prod);
    assign norm = prod << lz;

    // Ideal (pre-clamp) biased exponent of the normalised result.
    //   biased = expa + expb - 14 - lz   (fp16 bias 15, 11-bit significands)
    logic signed [11:0] ebias_norm;
    assign ebias_norm = $signed({6'b0, expa}) + $signed({6'b0, expb})
                      - 12'sd14 - $signed({7'b0, lz});

    // ---- rounding (normal + subnormal via a uniform right-shift) ---------- //
    // Keep the top 11 bits of `norm` (implicit + 10 mantissa). Normal results
    // need no shift; subnormal results right-shift by (1 - ebias_norm), with a
    // sticky bit gathered from everything shifted past the guard.
    logic        result_sub;
    logic [11:0] rshift;
    assign result_sub = (ebias_norm <= 12'sd0);
    assign rshift = result_sub ? (12'sd1 - ebias_norm) : 12'sd0;

    logic [15:0] result_bits;
    always_comb begin
        logic [10:0] keep;          // 11-bit significand kept (implicit+mantissa)
        logic        guard, round_b, sticky, lsb, round_up;
        logic [11:0] rounded;       // 12 bits to catch mantissa carry-out
        logic [9:0]  exp_final;
        logic [47:0] ext;           // norm zero-extended for safe large shifts
        logic [47:0] shifted;
        logic [47:0] lost_mask;

        keep = 11'b0; guard = 1'b0; round_b = 1'b0; sticky = 1'b0;
        lsb = 1'b0; round_up = 1'b0; rounded = 12'b0; exp_final = 10'b0;
        ext = 48'b0; shifted = 48'b0; lost_mask = 48'b0;

        if (rshift >= 12'd33) begin
            // Shifted entirely past the guard: discarded value is below a half-ULP
            // of the min subnormal, so the result rounds to signed zero.
            result_bits = {sy, 15'b0};
        end else begin
            ext     = {26'b0, norm};                 // norm in bits [21:0]
            shifted = ext >> rshift[5:0];             // align to the keep boundary
            keep    = shifted[21:11];                 // implicit + 10 mantissa bits
            guard   = shifted[10];
            round_b = shifted[9];
            // sticky: any 1 below the round bit, OR any bit lost to the rshift
            lost_mask = (rshift == 12'd0) ? 48'b0 : ((48'b1 << rshift[5:0]) - 48'b1);
            sticky    = (|shifted[8:0]) | (|(ext & lost_mask));
            lsb       = keep[0];
            round_up  = guard & (round_b | sticky | lsb);
            rounded   = {1'b0, keep} + {11'b0, round_up};

            if (result_sub) begin
                // Subnormal range: exp field is 0. Rounding can carry the leading
                // 1 up into the implicit-bit position -> the smallest normal.
                if (rounded[10] == 1'b1)
                    result_bits = {sy, 5'd1, rounded[9:0]};   // -> min normal
                else
                    result_bits = {sy, 5'd0, rounded[9:0]};   // stays subnormal
            end else begin
                exp_final = ebias_norm[9:0];
                if (rounded[11] == 1'b1)                       // mantissa carry-out
                    exp_final = exp_final + 10'd1;
                if (exp_final >= 10'd31)
                    result_bits = {sy, INF};                  // overflow -> Inf
                else
                    result_bits = {sy, exp_final[4:0], rounded[9:0]};
            end
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    always_comb begin
        if (a_nan || b_nan || (a_inf && b_zero) || (b_inf && a_zero))
            y = QNAN;
        else if (a_inf || b_inf)
            y = {sy, INF};
        else if (a_zero || b_zero)
            y = {sy, 15'b0};
        else
            y = result_bits;
    end
endmodule
