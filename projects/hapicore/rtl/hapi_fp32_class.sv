// HapiCore — fp32 classify (fclass) — KemetCore Phase 2 RTL
//
// Scalar RISC-V F-extension fclass: a 10-bit one-hot mask describing the operand.
//   bit0 -Inf  bit1 -normal  bit2 -subnormal  bit3 -0  bit4 +0
//   bit5 +subnormal  bit6 +normal  bit7 +Inf  bit8 signaling NaN  bit9 quiet NaN
// A NaN is signaling when its mantissa MSB (bit 22) is 0, quiet when 1.
//
// Verified bit-exact vs golden fp32_class — see tb/test_fp32_class.py. Combinational.

module hapi_fp32_class (
    input  logic [31:0] a,
    output logic [9:0]  y
);
    wire        sign = a[31];
    wire [7:0]  exp  = a[30:23];
    wire [22:0] man  = a[22:0];

    wire is_inf  = (exp == 8'hFF) && (man == 23'd0);
    wire is_nan  = (exp == 8'hFF) && (man != 23'd0);
    wire is_zero = (exp == 8'd0)  && (man == 23'd0);
    wire is_sub  = (exp == 8'd0)  && (man != 23'd0);
    wire is_norm = (exp != 8'd0)  && (exp != 8'hFF);
    wire snan    = is_nan && (man[22] == 1'b0);

    always_comb begin
        y = 10'd0;
        y[0] =  sign & is_inf;
        y[1] =  sign & is_norm;
        y[2] =  sign & is_sub;
        y[3] =  sign & is_zero;
        y[4] = ~sign & is_zero;
        y[5] = ~sign & is_sub;
        y[6] = ~sign & is_norm;
        y[7] = ~sign & is_inf;
        y[8] =  is_nan &  snan;
        y[9] =  is_nan & ~snan;
    end
endmodule
