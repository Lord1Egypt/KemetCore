// PtahConv — fp32 bias-add + ReLU epilogue — KemetCore Phase 2 RTL
//
// The standard convolution epilogue applied to N lanes in parallel:
//   s_i = x_i + bias_i        (correctly-rounded fp32 add, hapi_fp32_add)
//   y_i = relu(s_i)           (keep strictly-positive finite/Inf; else -> +0.0)
// ReLU forces +/-0, negatives and NaN to +0.0 (a well-defined max(0,.) with NaN
// mapped to 0). Purely combinational. Bit-exact vs golden ptah_conv.bias_relu.

module ptah_bias_relu #(
    parameter int N = 8
) (
    input  logic [32*N-1:0] x,       // N fp32 activations, x_i = x[32*i +: 32]
    input  logic [32*N-1:0] bias,    // N fp32 biases
    output logic [32*N-1:0] y        // N fp32 relu(x_i + bias_i)
);
    genvar i;
    generate
        for (i = 0; i < N; i++) begin : lane
            wire [31:0] s;
            hapi_fp32_add u_add (.a(x[32*i +: 32]), .b(bias[32*i +: 32]), .y(s));
            wire is_nan = (s[30:23] == 8'hFF) && (s[22:0] != 23'd0);
            wire pos_nz = (s[31] == 1'b0) && (s[30:0] != 31'd0) && !is_nan;
            assign y[32*i +: 32] = pos_nz ? s : 32'h0000_0000;
        end
    endgenerate
endmodule
