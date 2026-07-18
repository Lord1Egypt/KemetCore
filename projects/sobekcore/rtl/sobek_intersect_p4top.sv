module sobek_intersect_p4top (
    input  logic        clk,
    input  logic        rst_n,

    // Inputs
    input  logic        valid_in,
    input  logic [31:0] o0, o1, o2,
    input  logic [31:0] d0, d1, d2,
    input  logic [31:0] v0_0, v0_1, v0_2,
    input  logic [31:0] v1_0, v1_1, v1_2,
    input  logic [31:0] v2_0, v2_1, v2_2,

    // Outputs
    output logic        valid_out,
    output logic        hit,
    output logic [31:0] t,
    output logic [31:0] u,
    output logic [31:0] v,
    output logic [31:0] w
);
    // Input flops
    logic        valid_in_q;
    logic [31:0] o0_q, o1_q, o2_q;
    logic [31:0] d0_q, d1_q, d2_q;
    logic [31:0] v0_0_q, v0_1_q, v0_2_q;
    logic [31:0] v1_0_q, v1_1_q, v1_2_q;
    logic [31:0] v2_0_q, v2_1_q, v2_2_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_in_q <= 1'b0;
            o0_q <= 32'd0; o1_q <= 32'd0; o2_q <= 32'd0;
            d0_q <= 32'd0; d1_q <= 32'd0; d2_q <= 32'd0;
            v0_0_q <= 32'd0; v0_1_q <= 32'd0; v0_2_q <= 32'd0;
            v1_0_q <= 32'd0; v1_1_q <= 32'd0; v1_2_q <= 32'd0;
            v2_0_q <= 32'd0; v2_1_q <= 32'd0; v2_2_q <= 32'd0;
        end else begin
            valid_in_q <= valid_in;
            o0_q <= o0; o1_q <= o1; o2_q <= o2;
            d0_q <= d0; d1_q <= d1; d2_q <= d2;
            v0_0_q <= v0_0; v0_1_q <= v0_1; v0_2_q <= v0_2;
            v1_0_q <= v1_0; v1_1_q <= v1_1; v1_2_q <= v1_2;
            v2_0_q <= v2_0; v2_1_q <= v2_1; v2_2_q <= v2_2;
        end
    end

    // Core
    logic        valid_out_c;
    logic        hit_c;
    logic [31:0] t_c, u_c, v_c, w_c;

    sobek_intersect u_core (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(valid_in_q),
        .o0(o0_q), .o1(o1_q), .o2(o2_q),
        .d0(d0_q), .d1(d1_q), .d2(d2_q),
        .v0_0(v0_0_q), .v0_1(v0_1_q), .v0_2(v0_2_q),
        .v1_0(v1_0_q), .v1_1(v1_1_q), .v1_2(v1_2_q),
        .v2_0(v2_0_q), .v2_1(v2_1_q), .v2_2(v2_2_q),
        .valid_out(valid_out_c),
        .hit(hit_c),
        .t(t_c),
        .u(u_c),
        .v(v_c),
        .w(w_c)
    );

    // Output flops
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_out <= 1'b0;
            hit <= 1'b0;
            t <= 32'd0;
            u <= 32'd0;
            v <= 32'd0;
            w <= 32'd0;
        end else begin
            valid_out <= valid_out_c;
            hit <= hit_c;
            t <= t_c;
            u <= u_c;
            v <= v_c;
            w <= w_c;
        end
    end
endmodule
