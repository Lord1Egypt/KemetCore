// HapiCore — hapi_fp32_to_int registered wrapper for Phase 4 P&R
module hapi_fp32_to_int_p4top (
    input  logic        clk,
    input  logic [31:0] a,
    input  logic        is_signed,
    input  logic        truncate,
    output logic [31:0] y
);
    logic [31:0] a_r;
    logic        is_signed_r;
    logic        truncate_r;
    logic [31:0] y_w;
    logic [31:0] y_r;

    always_ff @(posedge clk) begin
        a_r <= a;
        is_signed_r <= is_signed;
        truncate_r <= truncate;
        y_r <= y_w;
    end

    hapi_fp32_to_int u_core (
        .a(a_r),
        .is_signed(is_signed_r),
        .truncate(truncate_r),
        .y(y_w)
    );

    assign y = y_r;
endmodule
