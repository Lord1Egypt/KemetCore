// HapiCore — bf16_to_fp32 Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_bf16_to_fp32_p4top (
    input  logic        clk,
    input  logic [15:0] a,
    output logic [31:0] y
);
    logic [15:0] a_reg;
    logic [31:0] y_next, y_reg;

    always_ff @(posedge clk) begin
        a_reg <= a;
        y_reg <= y_next;
    end

    hapi_bf16_to_fp32 core (
        .a(a_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
