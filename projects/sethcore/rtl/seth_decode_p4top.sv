// SethCore — registered P&R boundary top for seth_decode (KemetCore Phase 4 depth)
//
// seth_decode is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_decode is instantiated UNCHANGED.
module seth_decode_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] ins_in,
    output logic        reg_write_out,
    output logic        alu_src_imm_out,
    output logic        a_src_pc_out,
    output logic        mem_read_out,
    output logic        mem_write_out,
    output logic        branch_out,
    output logic        jump_out,
    output logic        jalr_out,
    output logic        is_mdu_out,
    output logic [1:0]  wb_sel_out
);
    logic [31:0] ins_q;
    
    logic        reg_write_c;
    logic        alu_src_imm_c;
    logic        a_src_pc_c;
    logic        mem_read_c;
    logic        mem_write_c;
    logic        branch_c;
    logic        jump_c;
    logic        jalr_c;
    logic        is_mdu_c;
    logic [1:0]  wb_sel_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            ins_q <= 32'd0;
        end else begin
            ins_q <= ins_in;
        end
    end

    seth_decode u_core (
        .ins(ins_q),
        .reg_write(reg_write_c),
        .alu_src_imm(alu_src_imm_c),
        .a_src_pc(a_src_pc_c),
        .mem_read(mem_read_c),
        .mem_write(mem_write_c),
        .branch(branch_c),
        .jump(jump_c),
        .jalr(jalr_c),
        .is_mdu(is_mdu_c),
        .wb_sel(wb_sel_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_write_out   <= 1'b0;
            alu_src_imm_out <= 1'b0;
            a_src_pc_out    <= 1'b0;
            mem_read_out    <= 1'b0;
            mem_write_out   <= 1'b0;
            branch_out      <= 1'b0;
            jump_out        <= 1'b0;
            jalr_out        <= 1'b0;
            is_mdu_out      <= 1'b0;
            wb_sel_out      <= 2'd0;
        end else begin
            reg_write_out   <= reg_write_c;
            alu_src_imm_out <= alu_src_imm_c;
            a_src_pc_out    <= a_src_pc_c;
            mem_read_out    <= mem_read_c;
            mem_write_out   <= mem_write_c;
            branch_out      <= branch_c;
            jump_out        <= jump_c;
            jalr_out        <= jalr_c;
            is_mdu_out      <= is_mdu_c;
            wb_sel_out      <= wb_sel_c;
        end
    end
endmodule
