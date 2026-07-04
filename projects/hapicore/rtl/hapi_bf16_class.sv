// HapiCore — bf16 classify (fclass) — KemetCore Phase 2 RTL
//
// RISC-V fclass at bfloat16 (1/8/7): 10-bit one-hot (same layout as fp32/fp16):
//   bit0 -Inf,1 -normal,2 -subnormal,3 -0,4 +0,5 +subnormal,6 +normal,7 +Inf,
//   8 sNaN,9 qNaN. Bit-exact vs golden bf16_class. Combinational.

module hapi_bf16_class (
    input  logic [15:0] a,
    output logic [9:0]  y
);
    wire        sign = a[15];
    wire [7:0]  exp  = a[14:7];
    wire [6:0]  man  = a[6:0];
    wire is_inf  = (exp == 8'hFF) && (man == 7'd0);
    wire is_nan  = (exp == 8'hFF) && (man != 7'd0);
    wire is_zero = (exp == 8'd0) && (man == 7'd0);
    wire is_sub  = (exp == 8'd0) && (man != 7'd0);
    wire is_norm = (exp != 8'd0) && (exp != 8'hFF);
    wire snan    = is_nan && (man[6] == 1'b0);
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
