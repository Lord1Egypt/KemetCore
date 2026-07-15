// SobekCore — sobek_scale registered wrapper for Phase 4 P&R
module sobek_scale_p4top (
    input  logic        clk,
    input  logic [31:0] s,
    input  logic [31:0] v0, v1, v2,
    output logic [31:0] c0, c1, c2
);
    logic [31:0] s_r, v0_r, v1_r, v2_r;
    logic [31:0] c0_w, c1_w, c2_w;
    logic [31:0] c0_r, c1_r, c2_r;

    always_ff @(posedge clk) begin
        s_r  <= s;
        v0_r <= v0;
        v1_r <= v1;
        v2_r <= v2;
        c0_r <= c0_w;
        c1_r <= c1_w;
        c2_r <= c2_w;
    end

    sobek_scale u_core (
        .s(s_r),
        .v0(v0_r), .v1(v1_r), .v2(v2_r),
        .c0(c0_w), .c1(c1_w), .c2(c2_w)
    );

    assign c0 = c0_r;
    assign c1 = c1_r;
    assign c2 = c2_r;
endmodule
