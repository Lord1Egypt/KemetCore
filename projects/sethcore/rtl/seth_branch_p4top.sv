// SethCore — registered P&R boundary top for seth_branch (KemetCore Phase 4 depth)
//
// seth_branch is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_branch is instantiated UNCHANGED.
module seth_branch_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [2:0]  funct3_in,
    input  logic [31:0] rs1_in,
    input  logic [31:0] rs2_in,
    output logic        taken_out
);
    logic [2:0]  funct3_q;
    logic [31:0] rs1_q, rs2_q;
    logic        taken_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            funct3_q <= 3'd0;
            rs1_q    <= 32'd0;
            rs2_q    <= 32'd0;
        end else begin
            funct3_q <= funct3_in;
            rs1_q    <= rs1_in;
            rs2_q    <= rs2_in;
        end
    end

    seth_branch u_core (
        .funct3(funct3_q),
        .rs1(rs1_q),
        .rs2(rs2_q),
        .taken(taken_c)
    );

    always_ff @(posedge clk) begin
        if (rst) taken_out <= 1'b0;
        else     taken_out <= taken_c;
    end
endmodule
