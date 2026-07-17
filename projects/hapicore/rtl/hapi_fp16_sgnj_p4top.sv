// P&R wrapper for HapiCore fp16 sgnj (KemetCore Phase 4 P&R)
//
// Wraps the combinational hapi_fp16_sgnj datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module hapi_fp16_sgnj_p4top (
    input  logic        clk,
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic [2:0]  rm,   // Reusing rm for op (0=sgnj, 1=sgnjn, 2=sgnjx)
    output logic [15:0] y
);
    logic [15:0] a_reg, b_reg;
    logic [2:0]  rm_reg;
    logic [15:0] y_comb;

    always_ff @(posedge clk) begin
        a_reg  <= a;
        b_reg  <= b;
        rm_reg <= rm;
        y      <= y_comb;
    end

    hapi_fp16_sgnj u_core (
        .a(a_reg),
        .b(b_reg),
        .op(rm_reg[1:0]),
        .y(y_comb)
    );
endmodule
