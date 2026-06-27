// HapiCore — fp16 (IEEE-754 half) adder (KemetCore Phase 2 RTL)
//
// Single-cycle combinational binary16 add with full IEEE-754 handling:
//   * larger-magnitude operand chosen by an unsigned compare of {exp,mantissa}
//   * effective add (like signs) or subtract (unlike signs); result sign = big's
//   * NaN propagation, Inf+Inf(opp sign) -> NaN, Inf+finite -> Inf
//   * subnormal INPUTS treated with their true value; exact cancellation -> +0
//   * round-to-nearest-ties-to-even, overflow -> Inf, underflow -> subnormal
//
// fp16 layout: [15] sign | [14:10] exponent (bias 15) | [9:0] mantissa.
// This is the bf16 adder widened to fp16's field sizes: 11-bit significands, a
// 20-bit alignment frame (1 carry + 11 significand + 8 guard), an 11-bit keep,
// and overflow at exp >= 31. The biased-exponent expression (exp_big - nshift + 1)
// is identical to bf16. Bit-exact against the Python golden
// hapi_fpu.fp_add(a, b, "fp16") (numpy float16) — see tb/test_fp16_add.py.
//
// Yosys-portable: no int'() casts, exact-width function ports, rounding in
// module-level always_comb.

module hapi_fp16_add (
    input  logic [15:0] a,
    input  logic [15:0] b,
    output logic [15:0] y
);
    // ---- field extraction ------------------------------------------------- //
    logic       sa, sb;
    logic [4:0] ea, eb;
    logic [9:0] ma, mb;
    assign sa = a[15];  assign ea = a[14:10];  assign ma = a[9:0];
    assign sb = b[15];  assign eb = b[14:10];  assign mb = b[9:0];

    logic a_zero, b_zero, a_inf, b_inf, a_nan, b_nan;
    assign a_zero = (ea == 5'h00) && (ma == 10'h000);
    assign b_zero = (eb == 5'h00) && (mb == 10'h000);
    assign a_inf  = (ea == 5'h1F) && (ma == 10'h000);
    assign b_inf  = (eb == 5'h1F) && (mb == 10'h000);
    assign a_nan  = (ea == 5'h1F) && (ma != 10'h000);
    assign b_nan  = (eb == 5'h1F) && (mb != 10'h000);

    localparam logic [15:0] QNAN = 16'h7E00;
    localparam logic [14:0] INF  = 15'h7C00;

    // ---- pick larger-magnitude operand (big) vs smaller (small) ----------- //
    // fp16 magnitude order == unsigned order of the low 15 bits {exp,mantissa}.
    logic a_is_big;
    assign a_is_big = (a[14:0] >= b[14:0]);

    logic       sbig, ssml;
    logic [4:0] ebig, esml;
    logic [9:0] mbig, msml;
    always_comb begin
        if (a_is_big) begin
            sbig = sa; ebig = ea; mbig = ma;
            ssml = sb; esml = eb; msml = mb;
        end else begin
            sbig = sb; ebig = eb; mbig = mb;
            ssml = sa; esml = ea; msml = ma;
        end
    end

    // 11-bit significands and effective exponents. exp==0 (zero OR subnormal) gets
    // implicit bit 0 and effective exponent 1; a true zero then has significand 0.
    logic        big_e0, sml_e0;
    assign big_e0 = (ebig == 5'h00);
    assign sml_e0 = (esml == 5'h00);
    logic [10:0] sig_big, sig_sml;
    logic [5:0]  exp_big, exp_sml;
    assign sig_big = big_e0 ? {1'b0, mbig} : {1'b1, mbig};
    assign sig_sml = sml_e0 ? {1'b0, msml} : {1'b1, msml};
    assign exp_big = big_e0 ? 6'd1 : {1'b0, ebig};
    assign exp_sml = sml_e0 ? 6'd1 : {1'b0, esml};

    logic       eff_sub;                 // operands have opposite signs
    assign eff_sub = sa ^ sb;
    logic [5:0] exp_diff;
    assign exp_diff = exp_big - exp_sml; // >= 0 by construction

    // ---- align the small operand into a 20-bit field ---------------------- //
    // sig at bits [18:8]; 8 guard bits below for exact alignment, bit19 = carry.
    logic [19:0] big_f, sml_full, sml_aligned;
    logic        align_sticky;
    assign big_f    = {1'b0, sig_big, 8'b0};
    assign sml_full = {1'b0, sig_sml, 8'b0};

    always_comb begin
        logic [4:0]  sh;
        logic [19:0] lost_mask;
        sh        = exp_diff[4:0];
        lost_mask = (20'b1 << sh) - 20'b1;
        if (exp_diff >= 6'd20) begin
            sml_aligned  = 20'b0;
            align_sticky = (sig_sml != 11'b0);
        end else begin
            sml_aligned  = sml_full >> sh;
            align_sticky = (|(sml_full & lost_mask));
        end
    end

    // ---- effective add / subtract ----------------------------------------- //
    logic [19:0] summ;     // magnitude (>= 0; big >= small guarantees no borrow)
    assign summ = eff_sub ? (big_f - sml_aligned) : (big_f + sml_aligned);

    // ---- leading-zero count of the 20-bit magnitude ----------------------- //
    function automatic logic [4:0] clz20(input logic [19:0] x);
        casez (x)
            20'b1???????????????????: clz20 = 5'd0;
            20'b01??????????????????: clz20 = 5'd1;
            20'b001?????????????????: clz20 = 5'd2;
            20'b0001????????????????: clz20 = 5'd3;
            20'b00001???????????????: clz20 = 5'd4;
            20'b000001??????????????: clz20 = 5'd5;
            20'b0000001?????????????: clz20 = 5'd6;
            20'b00000001????????????: clz20 = 5'd7;
            20'b000000001???????????: clz20 = 5'd8;
            20'b0000000001??????????: clz20 = 5'd9;
            20'b00000000001?????????: clz20 = 5'd10;
            20'b000000000001????????: clz20 = 5'd11;
            20'b0000000000001???????: clz20 = 5'd12;
            20'b00000000000001??????: clz20 = 5'd13;
            20'b000000000000001?????: clz20 = 5'd14;
            20'b0000000000000001????: clz20 = 5'd15;
            20'b00000000000000001???: clz20 = 5'd16;
            20'b000000000000000001??: clz20 = 5'd17;
            20'b0000000000000000001?: clz20 = 5'd18;
            20'b00000000000000000001: clz20 = 5'd19;
            default:                  clz20 = 5'd20;  // x == 0
        endcase
    endfunction

    logic [4:0]  nshift;
    logic [19:0] norm;          // left-justified so bit19 = leading 1
    assign nshift = clz20(summ);
    assign norm   = summ << nshift;

    // Ideal biased exponent of the normalised result (same form as bf16):
    //   big_f places sig at bit8 -> value = summ * 2^(exp_big-33); after left-
    //   justifying by nshift, biased = exp_big - nshift + 1.
    logic signed [11:0] ebias_norm;
    assign ebias_norm = $signed({6'b0, exp_big}) - $signed({7'b0, nshift}) + 12'sd1;

    logic        result_sub;
    logic [11:0] rshift;
    assign result_sub = (ebias_norm <= 12'sd0);
    assign rshift = result_sub ? (12'sd1 - ebias_norm) : 12'sd0;

    // ---- normalise + round (mirrors hapi_fp16_mul) ------------------------ //
    logic [15:0] arith_bits;
    always_comb begin
        logic [10:0] keep;
        logic        guard, round_b, sticky, lsb, round_up;
        logic [11:0] rounded;
        logic [9:0]  exp_final;
        logic [31:0] ext, shifted, lost_mask;
        logic [11:0] totalshift;

        keep = 11'b0; guard = 1'b0; round_b = 1'b0; sticky = 1'b0;
        lsb = 1'b0; round_up = 1'b0; rounded = 12'b0; exp_final = 10'b0;
        ext = 32'b0; shifted = 32'b0; lost_mask = 32'b0;
        // base shift of 1 puts norm's implicit bit (bit19) at frame bit18
        totalshift = 12'd1 + rshift;

        if (summ == 20'b0) begin
            arith_bits = 16'h0000;                 // exact cancellation -> +0
        end else if (totalshift >= 12'd28) begin
            arith_bits = {sbig, 15'b0};            // underflow past half-ULP -> 0
        end else begin
            ext     = {12'b0, norm};               // implicit 1 at bit19
            shifted = ext >> totalshift[4:0];
            keep    = shifted[18:8];
            guard   = shifted[7];
            round_b = shifted[6];
            lost_mask = (32'b1 << totalshift[4:0]) - 32'b1;
            sticky    = (|shifted[5:0]) | (|(ext & lost_mask)) | align_sticky;
            lsb       = keep[0];
            round_up  = guard & (round_b | sticky | lsb);
            rounded   = {1'b0, keep} + {11'b0, round_up};

            if (result_sub) begin
                if (rounded[10] == 1'b1)
                    arith_bits = {sbig, 5'd1, rounded[9:0]};   // -> min normal
                else
                    arith_bits = {sbig, 5'd0, rounded[9:0]};   // stays subnormal
            end else begin
                exp_final = ebias_norm[9:0];
                if (rounded[11] == 1'b1)
                    exp_final = exp_final + 10'd1;
                if (exp_final >= 10'd31)
                    arith_bits = {sbig, INF};                  // overflow -> Inf
                else
                    arith_bits = {sbig, exp_final[4:0], rounded[9:0]};
            end
        end
    end

    // ---- top-level special-case mux --------------------------------------- //
    always_comb begin
        if (a_nan || b_nan || (a_inf && b_inf && (sa != sb)))
            y = QNAN;
        else if (a_inf)
            y = {sa, INF};
        else if (b_inf)
            y = {sb, INF};
        else if (a_zero && b_zero)
            y = {(sa & sb), 15'b0};        // (-0)+(-0) = -0, else +0
        else
            y = arith_bits;
    end
endmodule
