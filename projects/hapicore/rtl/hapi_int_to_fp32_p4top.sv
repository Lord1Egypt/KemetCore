// HapiCore — int_to_fp32 Phase 4 hardening wrapper
// Registered boundaries to force synthesis to tech-map the combinational
// logic path between flip-flops.

module hapi_int_to_fp32_p4top (
    input  logic        clk,
    input  logic [31:0] x,
    input  logic        is_signed,
    output logic [31:0] y
);
    logic [31:0] x_reg;
    logic        is_signed_reg;
    logic [31:0] y_next, y_reg;

    always_ff @(posedge clk) begin
        x_reg         <= x;
        is_signed_reg <= is_signed;
        y_reg         <= y_next;
    end

    hapi_int_to_fp32 core (
        .x(x_reg),
        .is_signed(is_signed_reg),
        .y(y_next)
    );

    assign y = y_reg;

endmodule
