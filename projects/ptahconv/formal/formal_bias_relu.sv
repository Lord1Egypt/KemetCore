// PtahConv — FORMAL: ptah_bias_relu output is always non-negative and never NaN
// (ReLU maps negatives/±0/NaN -> +0), for ALL x,bias — every lane, all inputs.
module formal_bias_relu #(parameter int N = 4) (
    input logic [32*N-1:0] x, bias
);
    wire [32*N-1:0] y;
    ptah_bias_relu #(.N(N)) u (.x(x), .bias(bias), .y(y));
    genvar i;
    generate for (i = 0; i < N; i++) begin : g
        wire [31:0] yi = y[32*i +: 32];
        wire is_nan = (yi[30:23] == 8'hFF) && (yi[22:0] != 23'd0);
        always_comb begin
            assert (yi[31] == 1'b0);   // never negative
            assert (!is_nan);          // never NaN
        end
    end endgenerate
endmodule
