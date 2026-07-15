// SobekCore — sobek_ray_point registered wrapper for Phase 4 P&R
module sobek_ray_point_p4top (
    input  logic        clk,
    input  logic [31:0] o0, o1, o2,
    input  logic [31:0] t,
    input  logic [31:0] d0, d1, d2,
    output logic [31:0] p0, p1, p2
);
    logic [31:0] o0_r, o1_r, o2_r;
    logic [31:0] t_r;
    logic [31:0] d0_r, d1_r, d2_r;

    logic [31:0] p0_w, p1_w, p2_w;
    logic [31:0] p0_r, p1_r, p2_r;

    always_ff @(posedge clk) begin
        o0_r <= o0;
        o1_r <= o1;
        o2_r <= o2;
        t_r  <= t;
        d0_r <= d0;
        d1_r <= d1;
        d2_r <= d2;

        p0_r <= p0_w;
        p1_r <= p1_w;
        p2_r <= p2_w;
    end

    sobek_ray_point u_core (
        .o0(o0_r), .o1(o1_r), .o2(o2_r),
        .t(t_r),
        .d0(d0_r), .d1(d1_r), .d2(d2_r),
        .p0(p0_w), .p1(p1_w), .p2(p2_w)
    );

    assign p0 = p0_r;
    assign p1 = p1_r;
    assign p2 = p2_r;
endmodule
