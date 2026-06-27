// HapiCore — bf16 multiplier (KemetCore Phase 2 RTL)
//
// Single-cycle combinational bfloat16 multiply with full IEEE-754-style handling:
//   * sign = sign_a ^ sign_b
//   * NaN propagation, Inf*0 -> NaN, Inf*finite -> Inf, x*0 -> 0
//   * subnormal INPUTS (exp==0) treated with their true value (no flush-to-zero)
//   * round-to-nearest-ties-to-even on the exact 16-bit product
//   * overflow -> Inf, underflow -> subnormal/zero (with correct RNE)
//
// bf16 layout: [15] sign | [14:7] exponent (bias 127) | [6:0] mantissa.
// Bit-exact against the Python golden round_bf16(a*b) — see tb/test_bf16_mul.py.
//
// Yosys-portable: no int'() casts, function ports are exact-width, all rounding
// logic lives in module-level always_comb (no unpacked-array function ports).

module hapi_bf16_mul (
    input  logic [15:0] a,
    input  logic [15:0] b,
    output logic [15:0] y
);
    // ---- field extraction ------------------------------------------------- //
    logic        sa, sb, sy;
    logic [7:0]  ea, eb;
    logic [6:0]  ma, mb;
    assign sa = a[15];  assign ea = a[14:7];  assign ma = a[6:0];
    assign sb = b[15];  assign eb = b[14:7];  assign mb = b[6:0];
    assign sy = sa ^ sb;

    // class flags
    logic a_zero, b_zero, a_inf, b_inf, a_nan, b_nan, a_sub, b_sub;
    assign a_zero = (ea == 8'h00) && (ma == 7'h00);
    assign b_zero = (eb == 8'h00) && (mb == 7'h00);
    assign a_sub  = (ea == 8'h00) && (ma != 7'h00);
    assign b_sub  = (eb == 8'h00) && (mb != 7'h00);
    assign a_inf  = (ea == 8'hFF) && (ma == 7'h00);
    assign b_inf  = (eb == 8'hFF) && (mb == 7'h00);
    assign a_nan  = (ea == 8'hFF) && (ma != 7'h00);
    assign b_nan  = (eb == 8'hFF) && (mb != 7'h00);

    localparam logic [15:0] QNAN = 16'h7FC0;  // canonical quiet NaN
    localparam logic [15:0] INF  = 16'h7F80;

    // ---- significands & effective exponents ------------------------------- //
    // 8-bit significand {implicit, mantissa}; subnormals use implicit 0, exp 1.
    logic [7:0] siga, sigb;
    logic [8:0] expa, expb;   // signed-ish wide exponent (always >=1 here)
    assign siga = a_sub ? {1'b0, ma} : {1'b1, ma};
    assign sigb = b_sub ? {1'b0, mb} : {1'b1, mb};
    assign expa = a_sub ? 9'd1 : {1'b0, ea};
    assign expb = b_sub ? 9'd1 : {1'b0, eb};

    // exact 16-bit product of the two 8-bit significands
    logic [15:0] prod;
    assign prod = siga * sigb;

    // ---- leading-zero count of the 16-bit product ------------------------- //
    // prod is nonzero whenever both operands are nonzero (guaranteed on the
    // arithmetic path: zero/inf/nan operands are handled in the mux below).
    function automatic logic [4:0] clz16(input logic [15:0] x);
        logic [4:0] n;
        begin
            n = 5'd0;
            if (x[15] == 1'b0) begin
                casez (x)
                    16'b1???????????????: n = 5'd0;
                    16'b01??????????????: n = 5'd1;
                    16'b001?????????????: n = 5'd2;
                    16'b0001????????????: n = 5'd3;
                    16'b00001???????????: n = 5'd4;
                    16'b000001??????????: n = 5'd5;
                    16'b0000001?????????: n = 5'd6;
                    16'b00000001????????: n = 5'd7;
                    16'b000000001???????: n = 5'd8;
                    16'b0000000001??????: n = 5'd9;
                    16'b00000000001?????: n = 5'd10;
                    16'b000000000001????: n = 5'd11;
                    16'b0000000000001???: n = 5'd12;
                    16'b00000000000001??: n = 5'd13;
                    16'b000000000000001?: n = 5'd14;
                    16'b0000000000000001: n = 5'd15;
                    default:              n = 5'd16;  // x==0 (not reached here)
                endcase
            end else begin
                n = 5'd0;
            end
            clz16 = n;
        end
    endfunction

    logic [4:0]  lz;
    logic [15:0] norm;          // product left-normalised so bit15 = leading 1
    assign lz   = clz16(prod);
    assign norm = prod << lz;

    // Ideal (pre-clamp) biased exponent of the normalised result.
    //   value = norm[15:0] * 2^(expa+expb-253-lz) ; biased = expa+expb-126-lz
    logic signed [11:0] ebias_norm;
    assign ebias_norm = $signed({3'b0, expa}) + $signed({3'b0, expb})
                      - 12'sd126 - $signed({7'b0, lz});

    // ---- rounding (normal + subnormal via a uniform right-shift) ---------- //
    // We keep the top 8 bits of `norm` (implicit + 7 mantissa). For normal
    // results no shift; for subnormal results we right-shift by (1 - ebias_norm)
    // and collect a sticky bit from everything shifted past the guard.
    logic        result_sub;        // result lands in the subnormal range
    logic [11:0] rshift;            // extra right shift for denormalisation
    assign result_sub = (ebias_norm <= 12'sd0);
    assign rshift = result_sub ? (12'sd1 - ebias_norm) : 12'sd0;

    logic [15:0] result_bits;
    always_comb begin
        logic [7:0]  keep;          // 8-bit significand kept (implicit+mantissa)
        logic        guard, round_b, sticky, lsb, round_up;
        logic [8:0]  rounded;       // 9 bits to catch mantissa carry-out
        logic [9:0]  exp_final;
        logic [31:0] ext;           // norm zero-extended for safe large shifts
        logic [31:0] shifted;       // ext aligned right by rshift
        logic [31:0] lost_mask;     // low bits dropped by the rshift

        keep = 8'b0; guard = 1'b0; round_b = 1'b0; sticky = 1'b0;
        lsb = 1'b0; round_up = 1'b0; rounded = 9'b0; exp_final = 10'b0;
        ext = 32'b0; shifted = 32'b0; lost_mask = 32'b0;

        if (rshift >= 12'd24) begin
            // Shifted entirely past the guard: the discarded value is below a
            // half-ULP of the min subnormal, so the result rounds to signed zero.
            result_bits = {sy, 15'b0};
        end else begin
            ext     = {16'b0, norm};                 // norm in bits [15:0]
            shifted = ext >> rshift[4:0];            // align to the keep boundary
            keep    = shifted[15:8];                 // implicit + 7 mantissa bits
            guard   = shifted[7];
            round_b = shifted[6];
            // sticky: any 1 below the round bit, OR any bit lost to the rshift
            lost_mask = (rshift == 12'd0) ? 32'b0 : ((32'b1 << rshift[4:0]) - 32'b1);
            sticky    = (|shifted[5:0]) | (|(ext & lost_mask));
            lsb       = keep[0];
            round_up  = guard & (round_b | sticky | lsb);
            rounded   = {1'b0, keep} + {8'b0, round_up};

            if (result_sub) begin
                // Subnormal range: exp field is 0. Rounding can carry the leading
                // 1 up into the implicit-bit position -> the smallest normal.
                if (rounded[7] == 1'b1)
                    result_bits = {sy, 8'd1, rounded[6:0]};   // -> min normal
                else
                    result_bits = {sy, 8'd0, rounded[6:0]};   // stays subnormal
            end else begin
                exp_final = ebias_norm[9:0];
                if (rounded[8] == 1'b1)                       // mantissa carry-out
                    exp_final = exp_final + 10'd1;
                if (exp_final >= 10'd255)
                    result_bits = {sy, INF[14:0]};            // overflow -> Inf
                else
                    result_bits = {sy, exp_final[7:0], rounded[6:0]};
            end
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    always_comb begin
        if (a_nan || b_nan || (a_inf && b_zero) || (b_inf && a_zero))
            y = QNAN;
        else if (a_inf || b_inf)
            y = {sy, INF[14:0]};
        else if (a_zero || b_zero)
            y = {sy, 15'b0};
        else
            y = result_bits;
    end
endmodule
