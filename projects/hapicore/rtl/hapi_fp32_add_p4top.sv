// HapiCore — registered P&R boundary top for hapi_fp32_add (Phase 4 depth)
//
// hapi_fp32_add (correctly-rounded IEEE-754 binary32 add) is purely
// combinational. This wrapper latches the operands, drives the verified adder,
// and latches the result — a real reg -> logic -> reg path for ASAP7 place/
// route + timing closure. hapi_fp32_add is instantiated UNCHANGED (bit-exact).
module hapi_fp32_add_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] a_in,
    input  logic [31:0] b_in,
    output logic [31:0] y_out
);
    logic [31:0] a_q, b_q, y_c;

    always_ff @(posedge clk) begin
        if (rst) begin a_q <= 32'd0; b_q <= 32'd0; end
        else     begin a_q <= a_in;  b_q <= b_in;  end
    end

    hapi_fp32_add u_core (.a(a_q), .b(b_q), .y(y_c));

    always_ff @(posedge clk) begin
        if (rst) y_out <= 32'd0;
        else     y_out <= y_c;
    end
endmodule
