// ImentetCore — registered P&R boundary top for imentet_qk_score (Phase 4)
//
// imentet_qk_score (fp32 scaled dot-product attention score over a D=8 head tile)
// is purely combinational: 8 fp32 multiplies -> left-to-right fp32 add chain ->
// scale multiply. This wrapper latches the packed q/k vectors and scale, drives
// the verified combinational core, and latches the score — a real reg -> logic ->
// reg path for ASAP7 place/route and timing closure. Core instantiated UNCHANGED.
module imentet_qk_score_p4top #(
    parameter int D = 8
) (
    input  logic                clk,
    input  logic                rst,
    input  logic [32*D-1:0]     q_in,
    input  logic [32*D-1:0]     k_in,
    input  logic [31:0]         s_in,
    output logic [31:0]         score_out
);
    logic [32*D-1:0] q_q, k_q;
    logic [31:0]     s_q, score_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            q_q <= '0;
            k_q <= '0;
            s_q <= 32'd0;
        end else begin
            q_q <= q_in;
            k_q <= k_in;
            s_q <= s_in;
        end
    end

    imentet_qk_score #(.D(D)) u_core (.q(q_q), .k(k_q), .s(s_q), .score(score_c));

    always_ff @(posedge clk) begin
        if (rst) score_out <= 32'd0;
        else     score_out <= score_c;
    end
endmodule
