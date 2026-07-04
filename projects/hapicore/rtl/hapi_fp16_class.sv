// HapiCore — fp16 classify (fclass) — KemetCore Phase 2 RTL
//
// RISC-V F-extension fclass at half precision (the fp16 analogue of
// hapi_fp32_class): a 10-bit one-hot describing the operand's class.
//   bit0 -Inf, 1 -normal, 2 -subnormal, 3 -0, 4 +0, 5 +subnormal, 6 +normal,
//   7 +Inf, 8 signaling NaN, 9 quiet NaN.
// Bit-exact vs golden fp16_class. Combinational.

module hapi_fp16_class (
    input  logic [15:0] a,
    output logic [9:0]  y
);
    wire        sign = a[15];
    wire [4:0]  exp  = a[14:10];
    wire [9:0]  man  = a[9:0];

    wire is_inf  = (exp == 5'h1F) && (man == 10'd0);
    wire is_nan  = (exp == 5'h1F) && (man != 10'd0);
    wire is_zero = (exp == 5'd0)  && (man == 10'd0);
    wire is_sub  = (exp == 5'd0)  && (man != 10'd0);
    wire is_norm = (exp != 5'd0)  && (exp != 5'h1F);
    wire snan    = is_nan && (man[9] == 1'b0);

    assign y[0] =  sign && is_inf;
    assign y[1] =  sign && is_norm;
    assign y[2] =  sign && is_sub;
    assign y[3] =  sign && is_zero;
    assign y[4] = !sign && is_zero;
    assign y[5] = !sign && is_sub;
    assign y[6] = !sign && is_norm;
    assign y[7] = !sign && is_inf;
    assign y[8] = is_nan &&  snan;
    assign y[9] = is_nan && !snan;
endmodule
