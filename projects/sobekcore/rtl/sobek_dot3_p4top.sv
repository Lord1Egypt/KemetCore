// SobekCore — registered P&R boundary top for sobek_dot3 (KemetCore Phase 4)
//
// sobek_dot3 (fp32 3-element dot product) is purely combinational. This wrapper
// latches the six input operands, drives the verified combinational core, and
// latches the result — a genuine reg -> logic -> reg path for ASAP7 place/route
// and timing closure. sobek_dot3 is instantiated UNCHANGED (bit-exact behaviour).
module sobek_dot3_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] a0_in, a1_in, a2_in,
    input  logic [31:0] b0_in, b1_in, b2_in,
    output logic [31:0] y_out
);
    logic [31:0] a0_q, a1_q, a2_q, b0_q, b1_q, b2_q, y_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            a0_q <= 32'd0; a1_q <= 32'd0; a2_q <= 32'd0;
            b0_q <= 32'd0; b1_q <= 32'd0; b2_q <= 32'd0;
        end else begin
            a0_q <= a0_in; a1_q <= a1_in; a2_q <= a2_in;
            b0_q <= b0_in; b1_q <= b1_in; b2_q <= b2_in;
        end
    end

    sobek_dot3 u_core (
        .a0(a0_q), .a1(a1_q), .a2(a2_q),
        .b0(b0_q), .b1(b1_q), .b2(b2_q),
        .y(y_c)
    );

    always_ff @(posedge clk) begin
        if (rst) y_out <= 32'd0;
        else     y_out <= y_c;
    end
endmodule
