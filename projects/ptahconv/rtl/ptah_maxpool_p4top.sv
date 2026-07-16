module ptah_maxpool_p4top (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    input  logic [31:0] d,
    output logic [31:0] y
);
    logic [31:0] a_q, b_q, c_q, d_q;
    logic [31:0] y_c, y_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_q <= 32'd0; b_q <= 32'd0; c_q <= 32'd0; d_q <= 32'd0;
            y_q <= 32'd0;
        end else begin
            a_q <= a;
            b_q <= b;
            c_q <= c;
            d_q <= d;
            y_q <= y_c;
        end
    end

    ptah_maxpool u_core (
        .a(a_q),
        .b(b_q),
        .c(c_q),
        .d(d_q),
        .y(y_c)
    );

    assign y = y_q;
endmodule
