// SethCore — registered P&R boundary top for seth_imm (KemetCore Phase 4 depth)
//
// seth_imm is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_imm is instantiated UNCHANGED.
module seth_imm_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] ins_in,
    output logic [31:0] imm_out
);
    logic [31:0] ins_q;
    logic [31:0] imm_c;

    always_ff @(posedge clk) begin
        if (rst) ins_q <= 32'd0;
        else     ins_q <= ins_in;
    end

    seth_imm u_core (
        .ins(ins_q),
        .imm(imm_c)
    );

    always_ff @(posedge clk) begin
        if (rst) imm_out <= 32'd0;
        else     imm_out <= imm_c;
    end
endmodule
