module hapi_fp16_mul_p4top (
    input  logic        clk,
    input  logic [15:0] a,
    input  logic [15:0] b,
    output logic [15:0] y
);

    logic [15:0] a_q;
    logic [15:0] b_q;
    logic [15:0] y_d;
    logic [15:0] y_q;

    always_ff @(posedge clk) begin
        a_q <= a;
        b_q <= b;
        y_q <= y_d;
    end

    hapi_fp16_mul u_core (
        .a(a_q),
        .b(b_q),
        .y(y_d)
    );

    assign y = y_q;

endmodule
