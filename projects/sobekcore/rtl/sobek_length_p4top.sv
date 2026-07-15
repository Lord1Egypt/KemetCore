// SobekCore — sobek_length registered wrapper for Phase 4 P&R
module sobek_length_p4top (
    input  logic        clk,
    input  logic [31:0] v0, v1, v2,
    output logic [31:0] len
);
    logic [31:0] v0_r, v1_r, v2_r;
    logic [31:0] len_w;
    logic [31:0] len_r;

    always_ff @(posedge clk) begin
        v0_r <= v0;
        v1_r <= v1;
        v2_r <= v2;
        len_r <= len_w;
    end

    sobek_length u_core (
        .v0(v0_r), .v1(v1_r), .v2(v2_r),
        .len(len_w)
    );

    assign len = len_r;
endmodule
