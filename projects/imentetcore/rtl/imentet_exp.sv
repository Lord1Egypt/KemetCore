// ImentetCore — fp32 exp(x) unit for softmax (Phase 2 RTL)
//
// Computes e^x for x <= 0 using a fixed-order fp32 datapath.
// Approximates via y = x * log2(e), integer/fraction extraction,
// a 16-entry LUT for the upper 4 bits of the fraction, and a
// Taylor polynomial for the remainder.
//
// Bit-exact against imentet_fp32.exp_bits().

module imentet_exp (
    input  logic [31:0] x,
    output logic [31:0] y
);
    localparam logic [31:0] FP32_ZERO = 32'h00000000;
    localparam logic [31:0] FP32_ONE  = 32'h3F800000;
    localparam logic [31:0] FP32_LOG2_E = 32'h3FB8AA3B; // 1.44269504
    localparam logic [31:0] FP32_LN2 = 32'h3F317218;    // 0.69314718
    localparam logic [31:0] MIN_X = 32'hC2AEA09D;      // -87.33654 (approx)

    logic x_gt_0, x_lt_min;
    assign x_gt_0 = ~x[31] && (x[30:0] != 0);
    // Rough check for x < -87.33654
    // Exponent of 87 is 133 (85 in hex).
    // If exp > 133, or (exp == 133 && mantissa > ...). We can just use cmp.
    // Instead of instantiating hapi_fp32_cmp, we can just do a simple exponent check,
    // or just rely on the golden model's exact bounds.
    // Wait, the python model literally says `if x < -87.33654`.
    // Let's instantiate a full hapi_fp32_cmp for exactness.
    
    wire cmp_lt;
    hapi_fp32_cmp cmp_min (
        .a(x),
        .b(MIN_X),
        .op(2'b01), // flt (less than)
        .y(cmp_lt)
    );
    assign x_lt_min = cmp_lt;

    // 1. y = x * log2(e)
    wire [31:0] mul_y;
    hapi_fp32_mul u_mul_y (
        .a(x),
        .b(FP32_LOG2_E),
        .y(mul_y)
    );

    // 2. y_pos = -y
    wire [31:0] y_pos = {~mul_y[31], mul_y[30:0]};

    // 3. I_pos = int(y_pos)
    wire [31:0] i_pos;
    hapi_fp32_to_int u_to_int1 (
        .a(y_pos),
        .is_signed(1'b0),
        .truncate(1'b1), // int() in python truncates towards zero
        .y(i_pos)
    );

    // 4. f32_I_pos = f32(I_pos)
    wire [31:0] f32_i_pos;
    hapi_int_to_fp32 u_to_f32_1 (
        .x(i_pos),
        .is_signed(1'b0),
        .y(f32_i_pos)
    );

    // 5. F_pos = y_pos - f32_I_pos
    wire [31:0] f_pos;
    hapi_fp32_add u_sub_f (
        .a(y_pos),
        .b({~f32_i_pos[31], f32_i_pos[30:0]}),
        .y(f_pos)
    );

    // 6. I_shift and F_val
    wire f_pos_zero = (f_pos[30:0] == 0);
    wire [31:0] i_shift = f_pos_zero ? i_pos : (i_pos + 1);
    
    wire [31:0] f_val;
    hapi_fp32_add u_sub_fval (
        .a(FP32_ONE),
        .b({~f_pos[31], f_pos[30:0]}),
        .y(f_val)
    );
    wire [31:0] f_val_final = f_pos_zero ? FP32_ZERO : f_val;

    // 7. f_16 = f_val * 16.0
    // Multiply by 16 by adding 4 to exponent, watch out for zero
    wire [31:0] f_16 = (f_val_final[30:0] == 0) ? FP32_ZERO :
                       {f_val_final[31], f_val_final[30:23] + 8'd4, f_val_final[22:0]};

    // 8. idx = int(f_16)
    wire [31:0] idx;
    hapi_fp32_to_int u_to_int2 (
        .a(f_16),
        .is_signed(1'b0),
        .truncate(1'b1),
        .y(idx)
    );

    // 9. f32_idx = f32(idx)
    wire [31:0] f32_idx;
    hapi_int_to_fp32 u_to_f32_2 (
        .x(idx),
        .is_signed(1'b0),
        .y(f32_idx)
    );

    // 10. f32_idx_div_16
    wire [31:0] f32_idx_div_16 = (f32_idx[30:0] == 0) ? FP32_ZERO :
                                 {f32_idx[31], f32_idx[30:23] - 8'd4, f32_idx[22:0]};

    // 11. rem = F_val - f32_idx_div_16
    wire [31:0] rem;
    hapi_fp32_add u_sub_rem (
        .a(f_val_final),
        .b({~f32_idx_div_16[31], f32_idx_div_16[30:0]}),
        .y(rem)
    );

    // LUT
    logic [31:0] lut [0:15];
    assign lut[0] = 32'd1065353216;
    assign lut[1] = 32'd1065724611;
    assign lut[2] = 32'd1066112450;
    assign lut[3] = 32'd1066517459;
    assign lut[4] = 32'd1066940400;
    assign lut[5] = 32'd1067382066;
    assign lut[6] = 32'd1067843287;
    assign lut[7] = 32'd1068324927;
    assign lut[8] = 32'd1068827891;
    assign lut[9] = 32'd1069353124;
    assign lut[10]= 32'd1069901610;
    assign lut[11]= 32'd1070474380;
    assign lut[12]= 32'd1071072509;
    assign lut[13]= 32'd1071697119;
    assign lut[14]= 32'd1072349383;
    assign lut[15]= 32'd1073030525;
    
    wire [31:0] lut_val = lut[idx[3:0]];

    // 12. r_ln2 = rem * ln2
    wire [31:0] r_ln2;
    hapi_fp32_mul u_mul_r_ln2 (
        .a(rem),
        .b(FP32_LN2),
        .y(r_ln2)
    );

    // 13. r_ln2_sq = r_ln2 * r_ln2
    wire [31:0] r_ln2_sq;
    hapi_fp32_mul u_mul_r_ln2_sq (
        .a(r_ln2),
        .b(r_ln2),
        .y(r_ln2_sq)
    );

    // 14. term2 = 0.5 * r_ln2_sq
    wire [31:0] term2 = (r_ln2_sq[30:0] == 0) ? FP32_ZERO :
                        {r_ln2_sq[31], r_ln2_sq[30:23] - 8'd1, r_ln2_sq[22:0]};

    // 15. poly1 = r_ln2 + term2
    wire [31:0] poly1;
    hapi_fp32_add u_add_poly1 (
        .a(r_ln2),
        .b(term2),
        .y(poly1)
    );

    // 16. poly = 1.0 + poly1
    wire [31:0] poly;
    hapi_fp32_add u_add_poly2 (
        .a(FP32_ONE),
        .b(poly1),
        .y(poly)
    );

    // 17. res_unscaled = lut_val * poly
    wire [31:0] res_unscaled;
    hapi_fp32_mul u_mul_res (
        .a(lut_val),
        .b(poly),
        .y(res_unscaled)
    );

    // Exponent adjustment
    wire [7:0] exp_field = res_unscaled[30:23];
    wire [31:0] res_adjusted;
    
    assign res_adjusted = (exp_field >= i_shift[7:0]) ?
                          {res_unscaled[31], exp_field - i_shift[7:0], res_unscaled[22:0]} :
                          FP32_ZERO;

    assign y = x_gt_0 ? FP32_ONE :
               x_lt_min ? FP32_ZERO :
               res_adjusted;

endmodule
