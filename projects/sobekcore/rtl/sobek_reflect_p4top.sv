// SobekCore — sobek_reflect registered wrapper for Phase 4 P&R
module sobek_reflect_p4top (
    input  logic        clk,
    input  logic [31:0] d0, d1, d2,
    input  logic [31:0] n0, n1, n2,
    output logic [31:0] r0, r1, r2
);
    logic [31:0] d0_r, d1_r, d2_r;
    logic [31:0] n0_r, n1_r, n2_r;
    logic [31:0] r0_w, r1_w, r2_w;
    logic [31:0] r0_r, r1_r, r2_r;

    always_ff @(posedge clk) begin
        d0_r <= d0;
        d1_r <= d1;
        d2_r <= d2;
        n0_r <= n0;
        n1_r <= n1;
        n2_r <= n2;
        r0_r <= r0_w;
        r1_r <= r1_w;
        r2_r <= r2_w;
    end

    sobek_reflect u_core (
        .d0(d0_r), .d1(d1_r), .d2(d2_r),
        .n0(n0_r), .n1(n1_r), .n2(n2_r),
        .r0(r0_w), .r1(r1_w), .r2(r2_w)
    );

    assign r0 = r0_r;
    assign r1 = r1_r;
    assign r2 = r2_r;
endmodule
