// PtahConv — ptah_avgpool registered wrapper for Phase 4 P&R
module ptah_avgpool_p4top (
    input  logic        clk,
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    input  logic [31:0] d,
    output logic [31:0] y
);
    logic [31:0] a_r, b_r, c_r, d_r, y_w, y_r;

    always_ff @(posedge clk) begin
        a_r <= a;
        b_r <= b;
        c_r <= c;
        d_r <= d;
        y_r <= y_w;
    end

    ptah_avgpool u_core (
        .a(a_r),
        .b(b_r),
        .c(c_r),
        .d(d_r),
        .y(y_w)
    );

    assign y = y_r;
endmodule
