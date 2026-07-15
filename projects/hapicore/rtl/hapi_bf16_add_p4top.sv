// HapiCore — bf16 adder Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_bf16_add_p4top (
    input  logic        clk,
    input  logic [15:0] a,
    input  logic [15:0] b,
    output logic [15:0] y
);
    logic [15:0] a_reg, b_reg, y_next, y_reg;

    always_ff @(posedge clk) begin
        a_reg <= a;
        b_reg <= b;
        y_reg <= y_next;
    end

    hapi_bf16_add core (
        .a(a_reg),
        .b(b_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
