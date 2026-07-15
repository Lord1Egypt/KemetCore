// SobekCore — registered P&R boundary top for sobek_cross (KemetCore Phase 4)
//
// sobek_cross (fp32 3-element cross product) is purely combinational. This wrapper
// latches the six input operands, drives the verified combinational core, and
// latches the result — a genuine reg -> logic -> reg path for ASAP7 place/route
// and timing closure. sobek_cross is instantiated UNCHANGED (bit-exact behaviour).
module sobek_cross_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] a0_in, a1_in, a2_in,
    input  logic [31:0] b0_in, b1_in, b2_in,
    output logic [31:0] c0_out, c1_out, c2_out
);
    logic [31:0] a0_q, a1_q, a2_q, b0_q, b1_q, b2_q;
    logic [31:0] c0_c, c1_c, c2_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            a0_q <= 32'd0; a1_q <= 32'd0; a2_q <= 32'd0;
            b0_q <= 32'd0; b1_q <= 32'd0; b2_q <= 32'd0;
        end else begin
            a0_q <= a0_in; a1_q <= a1_in; a2_q <= a2_in;
            b0_q <= b0_in; b1_q <= b1_in; b2_q <= b2_in;
        end
    end

    sobek_cross u_core (
        .a0(a0_q), .a1(a1_q), .a2(a2_q),
        .b0(b0_q), .b1(b1_q), .b2(b2_q),
        .c0(c0_c), .c1(c1_c), .c2(c2_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            c0_out <= 32'd0;
            c1_out <= 32'd0;
            c2_out <= 32'd0;
        end else begin
            c0_out <= c0_c;
            c1_out <= c1_c;
            c2_out <= c2_c;
        end
    end
endmodule
