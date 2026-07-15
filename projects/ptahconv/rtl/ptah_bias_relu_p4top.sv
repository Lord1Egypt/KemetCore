module ptah_bias_relu_p4top #(
    parameter int N = 8
) (
    input  logic             clk,
    input  logic [32*N-1:0]  x,
    input  logic [32*N-1:0]  bias,
    output logic [32*N-1:0]  y
);
    logic [32*N-1:0] x_q;
    logic [32*N-1:0] bias_q;
    logic [32*N-1:0] y_d;
    logic [32*N-1:0] y_q;

    always_ff @(posedge clk) begin
        x_q    <= x;
        bias_q <= bias;
        y_q    <= y_d;
    end

    ptah_bias_relu #(
        .N(N)
    ) u_core (
        .x(x_q),
        .bias(bias_q),
        .y(y_d)
    );

    assign y = y_q;
endmodule
