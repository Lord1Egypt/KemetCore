// P&R wrapper for SobekCore distance (KemetCore Phase 4 P&R)
//
// Wraps the combinational sobek_distance datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module sobek_distance_p4top (
    input  logic        clk,
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] len
);
    logic [31:0] a0_reg, a1_reg, a2_reg;
    logic [31:0] b0_reg, b1_reg, b2_reg;
    logic [31:0] len_comb;

    always_ff @(posedge clk) begin
        a0_reg <= a0;
        a1_reg <= a1;
        a2_reg <= a2;
        b0_reg <= b0;
        b1_reg <= b1;
        b2_reg <= b2;
        len    <= len_comb;
    end

    sobek_distance u_core (
        .a0(a0_reg), .a1(a1_reg), .a2(a2_reg),
        .b0(b0_reg), .b1(b1_reg), .b2(b2_reg),
        .len(len_comb)
    );
endmodule
