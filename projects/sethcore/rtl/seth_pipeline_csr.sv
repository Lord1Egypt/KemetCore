// SethCore — 5-stage pipelined RV32IM core WITH FORWARDING (KemetCore Phase 2 RTL)
//
// Performance refinement of seth_pipeline: the broad interlock (which stalled the
// ID stage whenever a source register was the destination of *any* in-flight
// instruction) is replaced by data forwarding, so dependent instructions issue
// back-to-back with no bubbles. Architectural results are IDENTICAL to both the
// interlock pipeline and the golden ISA model — forwarding only changes timing.
//
// Forwarding network (all into the EX operands, newest producer wins):
//   * EX/MEM -> EX : a producer one instruction ahead (now in MEM) supplies its
//                    result m_wb_value. Loads are EXCLUDED here (their data is
//                    modelled as available only at WB) — covered by the load-use
//                    interlock + the MEM/WB path instead.
//   * MEM/WB -> EX : a producer two ahead (now in WB) supplies w_value (incl. loads).
//   * WB    -> ID  : a producer reaching WB the same cycle ID reads is bypassed at
//                    the read port (write-first behaviour) WITHOUT touching the
//                    shared seth_regfile — adding write-first there would form a
//                    combinational loop in the single-cycle core.
// The only remaining stall is the classic LOAD-USE hazard: a load in EX feeding the
// immediately-following instruction needs one bubble (its data isn't forwardable
// until WB). Branches/jumps still resolve in EX (2-cycle flush) using forwarded
// operands.
//
// Same external interface and TB methodology as seth_pipeline — see
// tb/test_pipeline_fwd.py (architectural equivalence + a cycle-count proof that
// forwarding strictly reduces stalls vs the interlock pipeline).

module seth_pipeline_csr #(
    parameter int WORDS = 1024
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        load_en,
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    input  logic        irq_soft,
    input  logic        irq_timer,
    input  logic        irq_ext,
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

    // WB->ID bypass (write-first): the synchronous regfile write commits on the same
    // edge ID would latch its read, so forward the WB datum at the read port here.
    logic [31:0] id_r1, id_r2;
    assign id_r1 = (wb_we && wb_rd == id_rs1 && id_rs1 != 5'd0) ? wb_value : id_rdata1;
    assign id_r2 = (wb_we && wb_rd == id_rs2 && id_rs2 != 5'd0) ? wb_value : id_rdata2;

    logic id_uses_rs1, id_uses_rs2;
    assign id_uses_rs1 = (id_op == 7'h33) || (id_op == 7'h13) || (id_op == 7'h03) ||
                         (id_op == 7'h23) || (id_op == 7'h63) || (id_op == 7'h67) || (id_op == 7'h73);
    assign id_uses_rs2 = (id_op == 7'h33) || (id_op == 7'h23) || (id_op == 7'h63);
    


    wire id_is_system = (id_op == 7'h73);
    wire id_is_csr    = id_is_system && (id_f3 != 3'd0);
    wire id_is_ecall  = id_is_system && (id_f3 == 3'd0) && (id_ins[31:20] == 12'h000);
    wire id_is_ebreak = id_is_system && (id_f3 == 3'd0) && (id_ins[31:20] == 12'h001);
    wire id_is_mret   = id_is_system && (id_f3 == 3'd0) && (id_ins[31:20] == 12'h302);
    wire id_is_wfi    = id_is_system && (id_f3 == 3'd0) && (id_ins[31:20] == 12'h105);
    wire id_is_legal  = (id_op == 7'h33) || (id_op == 7'h13) || (id_op == 7'h03) || (id_op == 7'h23)
                     || (id_op == 7'h63) || (id_op == 7'h37) || (id_op == 7'h17) || (id_op == 7'h6F)
                     || (id_op == 7'h67) || (id_op == 7'h73);
    wire id_is_illegal = ~id_is_legal;

    // ID/EX register additions
    // ============================ ID/EX register ========================== //
    logic        ex_valid, ex_rw, ex_alusrc, ex_apc, ex_mr, ex_mw, ex_br, ex_jmp, ex_jalr, ex_mdu, ex_ec;
    logic        ex_is_csr, ex_is_ecall, ex_is_ebreak, ex_is_mret, ex_is_wfi, ex_is_illegal;
    logic [11:0] ex_funct12;
    logic [1:0]  ex_wb;
    logic [3:0]  ex_aluop;
    logic [2:0]  ex_f3;
    logic [4:0]  ex_rd, ex_rs1, ex_rs2;
    logic [31:0] ex_pc, ex_imm, ex_r1, ex_r2, ex_ins_for_val;

    // ============================ EX ====================================== //

    // ---- CSR storage + WARL read ----------------------------------------- //
    localparam logic [11:0] MSTATUS=12'h300, MISA=12'h301, MIE=12'h304, MTVEC=12'h305,
                            MSCRATCH=12'h340, MEPC=12'h341, MCAUSE=12'h342, MTVAL=12'h343, MIP=12'h344;
    localparam logic [31:0] MISA_VAL=32'h4000_1100, MSTATUS_WMASK=(32'h1<<3)|(32'h1<<7),
                            MSTATUS_MPP=32'h3<<11, MIE_WMASK=(32'h1<<3)|(32'h1<<7)|(32'h1<<11);
    logic [31:0] mstatus_s, mtvec_s, mie_s, mscratch_s, mepc_s, mcause_s, mtval_s;
    wire [31:0] mip_val = ({31'd0, irq_soft} << 3) | ({31'd0, irq_timer} << 7) | ({31'd0, irq_ext} << 11);

    function automatic logic [31:0] csr_read(input logic [11:0] a);
        case (a)
            MSTATUS:  csr_read = (mstatus_s & MSTATUS_WMASK) | MSTATUS_MPP;
            MISA:     csr_read = MISA_VAL;
            MIE:      csr_read = mie_s & MIE_WMASK;
            MTVEC:    csr_read = mtvec_s;
            MSCRATCH: csr_read = mscratch_s;
            MEPC:     csr_read = mepc_s & 32'hFFFF_FFFE;
            MCAUSE:   csr_read = mcause_s;
            MTVAL:    csr_read = mtval_s;
            MIP:      csr_read = mip_val;
            default:  csr_read = 32'h0;
        endcase
    endfunction

    wire [31:0] csr_old  = csr_read(ex_funct12);
    wire [31:0] csr_oper = ex_f3[2] ? {27'd0, ex_rs1} : fwd_r1;
    logic [31:0] csr_raw; logic csr_we_raw;
    always_comb begin
        case (ex_f3[1:0])
            2'b01:   begin csr_raw = csr_oper;            csr_we_raw = ex_is_csr;                 end
            2'b10:   begin csr_raw = csr_old | csr_oper;  csr_we_raw = ex_is_csr && (csr_oper!=0); end
            2'b11:   begin csr_raw = csr_old & ~csr_oper; csr_we_raw = ex_is_csr && (csr_oper!=0); end
            default: begin csr_raw = csr_old;             csr_we_raw = 1'b0;                    end
        endcase
    end
    wire csr_we = csr_we_raw && ex_valid; // only write if valid

    // ---- trap vectoring --------------------------------------------------- //
    wire        m_ie   = mstatus_s[3];
    wire [31:0] ready  = mip_val & (mie_s & MIE_WMASK);
    // Interrupts evaluated in EX, prioritize over exceptions
    wire        take_int = m_ie && (|ready) && ex_valid;
    wire [30:0] int_cause = ready[11] ? 31'd11 : (ready[3] ? 31'd3 : 31'd7);
    
    wire [30:0] exc_cause  = ex_is_illegal ? 31'd2 : (ex_is_ebreak ? 31'd3 : 31'd11);
    wire        is_exc     = ex_is_ecall || ex_is_ebreak || ex_is_illegal;
    wire [30:0] trap_cause = take_int ? int_cause : exc_cause;
    wire        trap_isint = take_int;
    wire        do_enter   = take_int || (is_exc && ex_valid);
    wire        wfi_stall  = ex_is_wfi && ~(|(mip_val & (mie_s & MIE_WMASK))) && ~take_int && ex_valid;

    logic [31:0] enter_target, enter_mepc, enter_mcause, enter_mstatus, ret_target, ret_mstatus;
    seth_trap e_trap (
        .pc(ex_pc), .cause(trap_cause), .is_interrupt(trap_isint),
        .mtvec(csr_read(MTVEC)), .mstatus(csr_read(MSTATUS)), .mepc(csr_read(MEPC)),
        .enter_target(enter_target), .enter_mepc(enter_mepc), .enter_mcause(enter_mcause),
        .enter_mstatus(enter_mstatus), .ret_target(ret_target), .ret_mstatus(ret_mstatus));


    // EX/MEM and MEM/WB registers are declared below; forward muxes reference them.
    logic        m_valid, m_rw, m_mr, m_mw, m_ec;
    logic [1:0]  m_wb;
    logic [2:0]  m_f3;
    logic [4:0]  m_rd;
    logic [31:0] m_alu_y, m_r2, m_pc4, m_imm, m_compute;
    logic [31:0] m_wb_value;                       // forwardable value out of MEM
    logic        w_valid, w_rw, w_ec;
    logic [4:0]  w_rd;
    logic [31:0] w_value;

    // Forwarding muxes into the EX operands (newest producer first). The MEM source
    // is suppressed for loads (m_mr): a load's datum isn't ready to forward until WB.
    logic [31:0] fwd_r1, fwd_r2;
    always_comb begin
        fwd_r1 = ex_r1;
        if (ex_rs1 != 5'd0) begin
            if (m_valid && m_rw && !m_mr && m_rd == ex_rs1)      fwd_r1 = m_wb_value;
            else if (w_valid && w_rw && w_rd == ex_rs1)          fwd_r1 = w_value;
        end
        fwd_r2 = ex_r2;
        if (ex_rs2 != 5'd0) begin
            if (m_valid && m_rw && !m_mr && m_rd == ex_rs2)      fwd_r2 = m_wb_value;
            else if (w_valid && w_rw && w_rd == ex_rs2)          fwd_r2 = w_value;
        end
    end

    logic [31:0] ex_alu_a, ex_alu_b, ex_alu_y, ex_mdu_y, ex_compute;
    assign ex_alu_a = ex_apc ? ex_pc : fwd_r1;
    assign ex_alu_b = ex_alusrc ? ex_imm : fwd_r2;
    seth_alu    e_alu (.a(ex_alu_a), .b(ex_alu_b), .op(ex_aluop), .y(ex_alu_y));
    seth_muldiv e_mdu (.a(fwd_r1), .b(fwd_r2), .op(ex_f3), .y(ex_mdu_y));
    assign ex_compute = ex_is_csr ? csr_old : (ex_mdu ? ex_mdu_y : ex_alu_y);

    logic ex_take;
    always_comb begin
        unique case (ex_f3)
            3'h0:    ex_take = (fwd_r1 == fwd_r2);
            3'h1:    ex_take = (fwd_r1 != fwd_r2);
            3'h4:    ex_take = ($signed(fwd_r1) <  $signed(fwd_r2));
            3'h5:    ex_take = ($signed(fwd_r1) >= $signed(fwd_r2));
            3'h6:    ex_take = (fwd_r1 <  fwd_r2);
            3'h7:    ex_take = (fwd_r1 >= fwd_r2);
            default: ex_take = 1'b0;
        endcase
    end

    logic        redirect;
    logic [31:0] redirect_pc;
    assign redirect    = (ex_valid && (ex_jmp || (ex_br && ex_take))) || do_enter || (ex_valid && ex_is_mret) || wfi_stall;
    assign redirect_pc = do_enter ? enter_target : (ex_is_mret ? ret_target : (wfi_stall ? ex_pc : (ex_jmp ? (ex_jalr ? ((fwd_r1 + ex_imm) & ~32'd1) : (ex_pc + ex_imm)) : (ex_pc + ex_imm))));

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
    assign wb_we    = w_valid & w_rw & ~halted;
    assign wb_rd    = w_rd;
    assign wb_value = w_value;

    // ============================ hazard / control ======================== //
    // Only the load-use hazard remains: a load in EX feeding the instruction in ID.
    logic load_use, stall;
    assign load_use = id_valid && ex_valid && ex_mr && (ex_rd != 5'd0) &&
                      ((id_uses_rs1 && id_rs1 == ex_rd) ||
                       (id_uses_rs2 && id_rs2 == ex_rd));
    assign stall = (id_uses_rs1 && ex_mr && ex_rd == id_rs1 && id_rs1 != 5'd0) ||
                   (id_uses_rs2 && ex_mr && ex_rd == id_rs2 && id_rs2 != 5'd0);

    // ============================ sequential ============================== //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc <= 32'd0; halted <= 1'b0;
            id_valid <= 1'b0; ex_valid <= 1'b0; m_valid <= 1'b0; w_valid <= 1'b0;
            id_pc <= 32'd0; id_ins <= 32'd0;
            mstatus_s<=0; mtvec_s<=0; mie_s<=0; mscratch_s<=0; mepc_s<=0; mcause_s<=0; mtval_s<=0;
            mstatus_s<=0; mtvec_s<=0; mie_s<=0; mscratch_s<=0; mepc_s<=0; mcause_s<=0; mtval_s<=0;
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


            // ---- EX/MEM <- ID/EX ------------------------------------------ //
            m_valid   <= ex_valid;
            m_rw      <= ex_rw && !do_enter;
            m_mr      <= ex_mr;
            m_mw      <= ex_mw;
            m_ec      <= ex_ec;
            m_wb      <= ex_wb;
            m_f3      <= ex_f3;
            m_rd      <= ex_rd;
            m_alu_y   <= ex_alu_y;
            m_compute <= ex_compute;
            m_r2      <= fwd_r2;                    // forwarded store data
            m_pc4     <= ex_pc + 32'd4;
            m_imm     <= ex_imm;

            // ---- ID/EX <- ID  (bubble on stall or flush) ------------------ //
            if (stall || redirect) begin
                ex_valid <= 1'b0;
                ex_rw <= 1'b0; ex_mw <= 1'b0; ex_mr <= 1'b0; ex_br <= 1'b0;
                ex_jmp <= 1'b0; ex_jalr <= 1'b0; ex_mdu <= 1'b0; ex_ec <= 1'b0;
                ex_is_csr <= 1'b0; ex_is_ecall <= 1'b0; ex_is_ebreak <= 1'b0;
                ex_is_mret <= 1'b0; ex_is_wfi <= 1'b0; ex_is_illegal <= 1'b0;
            end else begin
                ex_valid  <= id_valid;
                ex_rw     <= id_rw || id_is_csr;     ex_alusrc <= id_alusrc; ex_apc <= id_apc;
                ex_mr     <= id_mr;     ex_mw     <= id_mw;     ex_br  <= id_br;
                ex_jmp    <= id_jmp;    ex_jalr   <= id_jalr;   ex_mdu <= id_mdu;
                ex_ec     <= id_is_ecall;
                ex_is_csr <= id_is_csr; ex_is_ecall <= id_is_ecall; ex_is_ebreak <= id_is_ebreak;
                ex_is_mret <= id_is_mret; ex_is_wfi <= id_is_wfi; ex_is_illegal <= id_is_illegal; ex_funct12 <= id_ins[31:20];
                ex_wb     <= id_wb;     ex_aluop  <= id_aluop;  ex_f3  <= id_f3;
                ex_rd     <= id_rd;     ex_pc     <= id_pc;     ex_imm <= id_imm; ex_ins_for_val <= id_ins;
                ex_rs1    <= id_rs1;    ex_rs2    <= id_rs2;
                ex_r1     <= id_r1;     ex_r2     <= id_r2;
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
            end else begin
                pc       <= pc + 32'd4;
                id_valid <= 1'b1;
                id_pc    <= pc;
                id_ins   <= if_ins;
            end

            // CSR writes and trap side-effects
            if (csr_we && !take_int) begin
                case (ex_funct12)
                    MSTATUS:  mstatus_s  <= csr_raw & MSTATUS_WMASK;
                    MIE:      mie_s      <= csr_raw & MIE_WMASK;
                    MTVEC:    mtvec_s    <= (csr_raw & 32'hFFFF_FFFC) | (csr_raw & 32'h1);
                    MSCRATCH: mscratch_s <= csr_raw;
                    MEPC:     mepc_s     <= csr_raw & 32'hFFFF_FFFE;
                    MCAUSE:   mcause_s   <= csr_raw;
                    MTVAL:    mtval_s    <= csr_raw;
                    default:  ;
                endcase
            end
            if (do_enter) begin
                mepc_s    <= enter_mepc;
                mcause_s  <= enter_mcause;
                mstatus_s <= enter_mstatus & MSTATUS_WMASK;
                mtval_s   <= take_int ? 32'd0 : (ex_is_illegal ? ex_ins_for_val : (ex_is_ebreak ? ex_pc : 32'd0));
            end
            if (ex_valid && ex_is_mret && !take_int) mstatus_s <= ret_mstatus & MSTATUS_WMASK;
        end
    end
endmodule
