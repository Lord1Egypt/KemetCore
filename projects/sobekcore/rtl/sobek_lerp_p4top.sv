// SobekCore — sobek_lerp registered wrapper for Phase 4 P&R
module sobek_lerp_p4top (
    input  logic        clk,
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    input  logic [31:0] t,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] a0_r, a1_r, a2_r;
    logic [31:0] b0_r, b1_r, b2_r;
    logic [31:0] t_r;

    logic [31:0] r0_w, r1_w, r2_w;
    logic [31:0] r0_r, r1_r, r2_r;

    always_ff @(posedge clk) begin
        a0_r <= a0;
        a1_r <= a1;
        a2_r <= a2;
        b0_r <= b0;
        b1_r <= b1;
        b2_r <= b2;
        t_r  <= t;

        r0_r <= r0_w;
        r1_r <= r1_w;
        r2_r <= r2_w;
    end

    sobek_lerp u_core (
        .a0(a0_r), .a1(a1_r), .a2(a2_r),
        .b0(b0_r), .b1(b1_r), .b2(b2_r),
        .t(t_r),
        .r0(r0_w), .r1(r1_w), .r2(r2_w)
    );

    assign r0 = r0_r;
    assign r1 = r1_r;
    assign r2 = r2_r;
endmodule
