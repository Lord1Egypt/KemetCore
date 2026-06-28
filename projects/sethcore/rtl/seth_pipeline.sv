// SethCore — 5-stage pipelined RV32IM core (KemetCore Phase 2 RTL)
//
// Classic IF / ID / EX / MEM / WB pipeline built on the same verified blocks as
// the single-cycle core (seth_decode, seth_imm, seth_aluctl, seth_alu,
// seth_muldiv, seth_regfile). Correctness is provided by full INTERLOCK STALLS
// (no forwarding yet): the ID stage stalls whenever a source register it reads is
// the destination of an instruction still in flight (EX/MEM/WB), so the register
// file always returns committed values. Branches and jumps resolve in EX and flush
// the two younger instructions (a 2-cycle control penalty). Final architectural
// state is identical to the ISA model (forwarding-invariant); forwarding is a
// later, performance-only refinement.
//
// Same external interface as seth_core: the testbench preloads program/data via
// the load_* port under reset, then runs to `halted` (an ecall reaching WB).
// Verified by comparing the full final register file to the golden — see
// tb/test_pipeline.py.

module seth_pipeline #(
    parameter int WORDS = 1024
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        load_en,
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    output logic [31:0] dbg_pc,
    output logic        halted
);
    localparam int AW = $clog2(WORDS);

    logic [31:0] wmem [0:WORDS-1];
    logic [31:0] pc;
    assign dbg_pc = pc;

    // ============================ IF ====================================== //
    logic [31:0] if_ins;
    assign if_ins = wmem[pc[AW+1:2]];

    // IF/ID pipeline register
    logic        id_valid;
    logic [31:0] id_pc, id_ins;

    // ============================ ID ====================================== //
    logic [4:0]  id_rs1, id_rs2, id_rd;
    logic [2:0]  id_f3;
    logic [6:0]  id_op;
    assign id_op  = id_ins[6:0];
    assign id_rs1 = id_ins[19:15];
    assign id_rs2 = id_ins[24:20];
    assign id_rd  = id_ins[11:7];
    assign id_f3  = id_ins[14:12];

    logic id_rw, id_alusrc, id_apc, id_mr, id_mw, id_br, id_jmp, id_jalr, id_mdu;
    logic [1:0] id_wb;
    seth_decode u_dec (.ins(id_ins), .reg_write(id_rw), .alu_src_imm(id_alusrc),
        .a_src_pc(id_apc), .mem_read(id_mr), .mem_write(id_mw), .branch(id_br),
        .jump(id_jmp), .jalr(id_jalr), .is_mdu(id_mdu), .wb_sel(id_wb));

    logic [31:0] id_imm;
    seth_imm u_imm (.ins(id_ins), .imm(id_imm));

    logic [3:0] id_aluop;
    seth_aluctl u_actl (.opcode(id_op), .funct3(id_f3), .funct7(id_ins[31:25]), .alu_op(id_aluop));

    logic [31:0] id_rdata1, id_rdata2, wb_value;
    logic        wb_we;
    logic [4:0]  wb_rd;
    seth_regfile u_rf (.clk(clk), .rst(rst), .we(wb_we), .waddr(wb_rd), .wdata(wb_value),
        .raddr1(id_rs1), .raddr2(id_rs2), .rdata1(id_rdata1), .rdata2(id_rdata2));

    logic id_uses_rs1, id_uses_rs2, id_is_ecall;
    assign id_uses_rs1 = (id_op == 7'h33) || (id_op == 7'h13) || (id_op == 7'h03) ||
                         (id_op == 7'h23) || (id_op == 7'h63) || (id_op == 7'h67);
    assign id_uses_rs2 = (id_op == 7'h33) || (id_op == 7'h23) || (id_op == 7'h63);
    assign id_is_ecall = (id_op == 7'h73);

    // ============================ ID/EX register ========================== //
    logic        ex_valid, ex_rw, ex_alusrc, ex_apc, ex_mr, ex_mw, ex_br, ex_jmp, ex_jalr, ex_mdu, ex_ec;
    logic [1:0]  ex_wb;
    logic [3:0]  ex_aluop;
    logic [2:0]  ex_f3;
    logic [4:0]  ex_rd;
    logic [31:0] ex_pc, ex_imm, ex_r1, ex_r2;

    // ============================ EX ====================================== //
    logic [31:0] ex_alu_a, ex_alu_b, ex_alu_y, ex_mdu_y, ex_compute;
    assign ex_alu_a = ex_apc ? ex_pc : ex_r1;
    assign ex_alu_b = ex_alusrc ? ex_imm : ex_r2;
    seth_alu    e_alu (.a(ex_alu_a), .b(ex_alu_b), .op(ex_aluop), .y(ex_alu_y));
    seth_muldiv e_mdu (.a(ex_r1), .b(ex_r2), .op(ex_f3), .y(ex_mdu_y));
    assign ex_compute = ex_mdu ? ex_mdu_y : ex_alu_y;

    logic ex_take;
    always_comb begin
        unique case (ex_f3)
            3'h0:    ex_take = (ex_r1 == ex_r2);
            3'h1:    ex_take = (ex_r1 != ex_r2);
            3'h4:    ex_take = ($signed(ex_r1) <  $signed(ex_r2));
            3'h5:    ex_take = ($signed(ex_r1) >= $signed(ex_r2));
            3'h6:    ex_take = (ex_r1 <  ex_r2);
            3'h7:    ex_take = (ex_r1 >= ex_r2);
            default: ex_take = 1'b0;
        endcase
    end

    logic        redirect;
    logic [31:0] redirect_pc;
    assign redirect    = ex_valid && (ex_jmp || (ex_br && ex_take));
    assign redirect_pc = ex_jmp ? (ex_jalr ? ((ex_r1 + ex_imm) & ~32'd1) : (ex_pc + ex_imm))
                                : (ex_pc + ex_imm);

    // ============================ EX/MEM register ========================= //
    logic        m_valid, m_rw, m_mr, m_mw, m_ec;
    logic [1:0]  m_wb;
    logic [2:0]  m_f3;
    logic [4:0]  m_rd;
    logic [31:0] m_alu_y, m_r2, m_pc4, m_imm, m_compute;

    // ============================ MEM ===================================== //
    logic [31:0] m_word, m_load_fmt, boff;
    assign m_word = wmem[m_alu_y[AW+1:2]];
    assign boff   = {27'b0, m_alu_y[1:0], 3'b0};
    always_comb begin
        logic [31:0] sh;
        sh = m_word >> boff[4:0];
        unique case (m_f3)
            3'h0:    m_load_fmt = {{24{sh[7]}},  sh[7:0]};
            3'h1:    m_load_fmt = {{16{sh[15]}}, sh[15:0]};
            3'h2:    m_load_fmt = m_word;
            3'h4:    m_load_fmt = {24'b0, sh[7:0]};
            3'h5:    m_load_fmt = {16'b0, sh[15:0]};
            default: m_load_fmt = m_word;
        endcase
    end

    logic [31:0] m_wb_value;
    always_comb begin
        unique case (m_wb)
            2'd0:    m_wb_value = m_compute;
            2'd1:    m_wb_value = m_load_fmt;
            2'd2:    m_wb_value = m_pc4;
            default: m_wb_value = m_imm;
        endcase
    end

    // store byte-merge (write in MEM stage)
    logic [31:0] m_store_word;
    always_comb begin
        logic [31:0] cur;
        cur = m_word;
        unique case (m_f3)
            3'h0:    m_store_word = (cur & ~(32'hFF   << boff[4:0])) | ((m_r2 & 32'hFF)   << boff[4:0]);
            3'h1:    m_store_word = (cur & ~(32'hFFFF << boff[4:0])) | ((m_r2 & 32'hFFFF) << boff[4:0]);
            default: m_store_word = m_r2;
        endcase
    end

    // ============================ MEM/WB register ========================= //
    logic        w_valid, w_rw, w_ec;
    logic [4:0]  w_rd;
    logic [31:0] w_value;
    assign wb_we    = w_valid & w_rw & ~halted;
    assign wb_rd    = w_rd;
    assign wb_value = w_value;

    // ============================ hazard / control ======================== //
    logic hz1, hz2, stall;
    assign hz1 = (id_rs1 != 5'd0) && (
                   (ex_valid && ex_rw && ex_rd == id_rs1) ||
                   (m_valid  && m_rw  && m_rd  == id_rs1) ||
                   (w_valid  && w_rw  && w_rd  == id_rs1));
    assign hz2 = (id_rs2 != 5'd0) && (
                   (ex_valid && ex_rw && ex_rd == id_rs2) ||
                   (m_valid  && m_rw  && m_rd  == id_rs2) ||
                   (w_valid  && w_rw  && w_rd  == id_rs2));
    assign stall = id_valid && ((id_uses_rs1 && hz1) || (id_uses_rs2 && hz2));

    // ============================ sequential ============================== //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc <= 32'd0; halted <= 1'b0;
            id_valid <= 1'b0; ex_valid <= 1'b0; m_valid <= 1'b0; w_valid <= 1'b0;
            id_pc <= 32'd0; id_ins <= 32'd0;
        end else if (load_en) begin
            wmem[load_addr[AW+1:2]] <= load_data;
        end else if (!halted) begin
            // ---- WB write happens via regfile (wb_we); MEM/WB <- EX/MEM ----- //
            w_valid <= m_valid;
            w_rw    <= m_valid && m_rw;
            w_rd    <= m_rd;
            w_value <= m_wb_value;
            w_ec    <= m_valid && m_ec;
            if (m_valid && m_mw)
                wmem[m_alu_y[AW+1:2]] <= m_store_word;
            if (m_valid && m_ec)
                halted <= 1'b1;

            // ---- EX/MEM <- ID/EX ------------------------------------------ //
            m_valid   <= ex_valid;
            m_rw      <= ex_rw;
            m_mr      <= ex_mr;
            m_mw      <= ex_mw;
            m_ec      <= ex_ec;
            m_wb      <= ex_wb;
            m_f3      <= ex_f3;
            m_rd      <= ex_rd;
            m_alu_y   <= ex_alu_y;
            m_compute <= ex_compute;
            m_r2      <= ex_r2;
            m_pc4     <= ex_pc + 32'd4;
            m_imm     <= ex_imm;

            // ---- ID/EX <- ID  (bubble on stall or flush) ------------------ //
            if (stall || redirect) begin
                ex_valid <= 1'b0;
                ex_rw <= 1'b0; ex_mw <= 1'b0; ex_mr <= 1'b0; ex_br <= 1'b0;
                ex_jmp <= 1'b0; ex_jalr <= 1'b0; ex_mdu <= 1'b0; ex_ec <= 1'b0;
            end else begin
                ex_valid  <= id_valid;
                ex_rw     <= id_rw;     ex_alusrc <= id_alusrc; ex_apc <= id_apc;
                ex_mr     <= id_mr;     ex_mw     <= id_mw;     ex_br  <= id_br;
                ex_jmp    <= id_jmp;    ex_jalr   <= id_jalr;   ex_mdu <= id_mdu;
                ex_ec     <= id_is_ecall;
                ex_wb     <= id_wb;     ex_aluop  <= id_aluop;  ex_f3  <= id_f3;
                ex_rd     <= id_rd;     ex_pc     <= id_pc;     ex_imm <= id_imm;
                ex_r1     <= id_rdata1; ex_r2     <= id_rdata2;
            end

            // ---- IF/ID  +  PC --------------------------------------------- //
            if (redirect) begin
                pc       <= redirect_pc;
                id_valid <= 1'b0;                 // flush wrong-path fetch
                id_ins   <= 32'd0;
            end else if (stall) begin
                // freeze PC and IF/ID (hold the stalled instruction)
                pc       <= pc;
                id_valid <= id_valid;
                id_pc    <= id_pc;
                id_ins   <= id_ins;
            end else if (id_valid && id_is_ecall) begin
                // ecall enters EX (via the ID/EX block above); stop fetching past it
                pc       <= pc;
                id_valid <= 1'b0;
                id_ins   <= 32'd0;
            end else begin
                pc       <= pc + 32'd4;
                id_valid <= 1'b1;
                id_pc    <= pc;
                id_ins   <= if_ins;
            end
        end
    end
endmodule
