// HapiCore — fp32_minmax Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_fp32_minmax_p4top (
    input  logic        clk,
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic        op,
    output logic [31:0] y
);
    logic [31:0] a_reg, b_reg;
    logic        op_reg;
    logic [31:0] y_next, y_reg;

    always_ff @(posedge clk) begin
        a_reg  <= a;
        b_reg  <= b;
        op_reg <= op;
        y_reg  <= y_next;
    end

    hapi_fp32_minmax core (
        .a(a_reg),
        .b(b_reg),
        .op(op_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
