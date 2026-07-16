// HapiCore — fp16_cmp Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_fp16_cmp_p4top (
    input  logic        clk,
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic [1:0]  op,
    output logic        y
);
    logic [15:0] a_reg, b_reg;
    logic [1:0]  op_reg;
    logic        y_next, y_reg;

    always_ff @(posedge clk) begin
        a_reg  <= a;
        b_reg  <= b;
        op_reg <= op;
        y_reg  <= y_next;
    end

    hapi_fp16_cmp core (
        .a(a_reg),
        .b(b_reg),
        .op(op_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
