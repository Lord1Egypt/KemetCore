// HapiCore — fp32_class Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_fp32_class_p4top (
    input  logic        clk,
    input  logic [31:0] a,
    output logic [9:0]  y
);
    logic [31:0] a_reg;
    logic [9:0]  y_next, y_reg;

    always_ff @(posedge clk) begin
        a_reg <= a;
        y_reg <= y_next;
    end

    hapi_fp32_class core (
        .a(a_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
