// SethCore — single-cycle RV32IMZicsr core (CSR + traps) — KemetCore Phase 2 RTL
//
// seth_core extended with the Zicsr machine-mode subset: it executes CSR
// instructions (csrrw/csrrs/csrrc + immediate) and takes/returns from M-mode traps
// (ecall/ebreak -> mtvec handler; mret -> mepc), using the same WARL CSR storage as
// seth_mcsr and the seth_trap vectoring unit. Unlike the RV32IM seth_core (which
// halts on any 0x73), here 0x73 is CSR/trap/mret and the core keeps running, so
// test programs finish in a self-loop and are compared to the CpuZ golden after a
// fixed number of cycles. Single-cycle => no hazards.
//
// Verified vs golden seth_rv32im_zicsr.CpuZ — see tb/test_core_csr.py.

module seth_core_csr #(
    parameter int WORDS = 1024
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        load_en,
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    input  logic        irq_soft,      // machine software interrupt (mip.MSIP)
    input  logic        irq_timer,     // machine timer interrupt    (mip.MTIP)
    input  logic        irq_ext,       // machine external interrupt (mip.MEIP)
    output logic [31:0] dbg_pc
);
    localparam int AW = $clog2(WORDS);
    logic [31:0] wmem [0:WORDS-1];
    logic [31:0] pc;
    assign dbg_pc = pc;

    // ---- fetch / fields --------------------------------------------------- //
    wire [31:0] ins = wmem[pc[AW+1:2]];
    wire [6:0]  op  = ins[6:0];
    wire [4:0]  rs1 = ins[19:15];
    wire [4:0]  rs2 = ins[24:20];
    wire [4:0]  rd  = ins[11:7];
    wire [2:0]  f3  = ins[14:12];
    wire [11:0] funct12 = ins[31:20];

    // ---- decode + control (shared building blocks) ------------------------ //
    logic reg_write, alu_src_imm, a_src_pc, mem_read, mem_write, branch, jump, jalr, is_mdu;
    logic [1:0] wb_sel;
    seth_decode u_dec (
        .ins(ins), .reg_write(reg_write), .alu_src_imm(alu_src_imm), .a_src_pc(a_src_pc),
        .mem_read(mem_read), .mem_write(mem_write), .branch(branch), .jump(jump),
        .jalr(jalr), .is_mdu(is_mdu), .wb_sel(wb_sel));
    logic [31:0] imm;   seth_imm u_imm (.ins(ins), .imm(imm));
    logic [3:0] alu_op; seth_aluctl u_actl (.opcode(op), .funct3(f3), .funct7(ins[31:25]), .alu_op(alu_op));

    // ---- system-instruction classification -------------------------------- //
    wire is_system = (op == 7'h73);
    wire is_csr    = is_system && (f3 != 3'd0);
    wire is_ecall  = is_system && (f3 == 3'd0) && (funct12 == 12'h000);
    wire is_ebreak = is_system && (f3 == 3'd0) && (funct12 == 12'h001);
    wire is_mret   = is_system && (f3 == 3'd0) && (funct12 == 12'h302);
    // any opcode outside the RV32IM + Zicsr set is illegal -> exception (cause 2)
    wire is_legal  = (op == 7'h33) || (op == 7'h13) || (op == 7'h03) || (op == 7'h23)
                  || (op == 7'h63) || (op == 7'h37) || (op == 7'h17) || (op == 7'h6F)
                  || (op == 7'h67) || (op == 7'h73);
    wire is_illegal = ~is_legal;
    wire is_exc    = is_ecall || is_ebreak || is_illegal;   // synchronous exception

    // asynchronous machine interrupts: taken at the instruction boundary when
    // globally (mstatus.MIE) and individually (mie) enabled; priority MEI>MSI>MTI.
    wire        m_ie   = mstatus_s[3];
    wire [31:0] ready  = mip_val & (mie_s & MIE_WMASK);
    wire        take_int = m_ie && (|ready);
    wire [30:0] int_cause = ready[11] ? 31'd11 : (ready[3] ? 31'd3 : 31'd7);
    wire        do_enter = take_int || is_exc;              // any trap entry this cycle

    // ---- CSR storage + WARL read (same policy as seth_mcsr) ---------------- //
    localparam logic [11:0] MSTATUS=12'h300, MISA=12'h301, MIE=12'h304, MTVEC=12'h305,
                            MSCRATCH=12'h340, MEPC=12'h341, MCAUSE=12'h342, MTVAL=12'h343, MIP=12'h344;
    localparam logic [31:0] MISA_VAL=32'h4000_1100, MSTATUS_WMASK=(32'h1<<3)|(32'h1<<7),
                            MSTATUS_MPP=32'h3<<11, MIE_WMASK=(32'h1<<3)|(32'h1<<7)|(32'h1<<11);
    logic [31:0] mstatus_s, mtvec_s, mie_s, mscratch_s, mepc_s, mcause_s, mtval_s;
    // machine interrupt-pending vector, driven by the external interrupt lines
    wire [31:0] mip_val = ({31'd0, irq_soft} << 3) | ({31'd0, irq_timer} << 7)
                        | ({31'd0, irq_ext} << 11);

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
            MIP:      csr_read = mip_val;    // read-only (writes ignored, WARL)
            default:  csr_read = 32'h0;
        endcase
    endfunction

    wire [31:0] csr_old  = csr_read(funct12);
    wire [31:0] csr_oper = f3[2] ? {27'd0, rs1} : rdata1;   // imm form: rs1 field = uimm
    logic [31:0] csr_raw; logic csr_we;
    always_comb begin
        case (f3[1:0])
            2'b01:   begin csr_raw = csr_oper;            csr_we = is_csr;                 end
            2'b10:   begin csr_raw = csr_old | csr_oper;  csr_we = is_csr && (csr_oper!=0); end
            2'b11:   begin csr_raw = csr_old & ~csr_oper; csr_we = is_csr && (csr_oper!=0); end
            default: begin csr_raw = csr_old;             csr_we = 1'b0;                    end
        endcase
    end

    // ---- trap vectoring --------------------------------------------------- //
    // interrupts preempt the instruction's own exception; pick the cause + kind
    wire [30:0] exc_cause  = is_illegal ? 31'd2 : (is_ebreak ? 31'd3 : 31'd11);
    wire [30:0] trap_cause = take_int ? int_cause : exc_cause;
    wire        trap_isint = take_int;
    logic [31:0] enter_target, enter_mepc, enter_mcause, enter_mstatus, ret_target, ret_mstatus;
    seth_trap u_trap (
        .pc(pc), .cause(trap_cause), .is_interrupt(trap_isint),
        .mtvec(csr_read(MTVEC)), .mstatus(csr_read(MSTATUS)), .mepc(csr_read(MEPC)),
        .enter_target(enter_target), .enter_mepc(enter_mepc), .enter_mcause(enter_mcause),
        .enter_mstatus(enter_mstatus), .ret_target(ret_target), .ret_mstatus(ret_mstatus));

    // ---- register read/write ---------------------------------------------- //
    logic [31:0] rdata1, rdata2, wb_data, wb_data_final;
    wire reg_write_final = (reg_write | is_csr) & ~load_en & ~do_enter;  // CSR writes rd; traps write nothing
    seth_regfile u_rf (
        .clk(clk), .rst(rst), .we(reg_write_final), .waddr(rd), .wdata(wb_data_final),
        .raddr1(rs1), .raddr2(rs2), .rdata1(rdata1), .rdata2(rdata2));

    // ---- execute ---------------------------------------------------------- //
    wire [31:0] alu_a = a_src_pc ? pc : rdata1;
    wire [31:0] alu_b = alu_src_imm ? imm : rdata2;
    logic [31:0] alu_y, mdu_y;
    seth_alu    u_alu (.a(alu_a), .b(alu_b), .op(alu_op), .y(alu_y));
    seth_muldiv u_mdu (.a(rdata1), .b(rdata2), .op(f3), .y(mdu_y));
    wire [31:0] compute = is_mdu ? mdu_y : alu_y;

    // ---- load formatting -------------------------------------------------- //
    wire [31:0] mem_word = wmem[alu_y[AW+1:2]];
    wire [4:0]  boff     = {alu_y[1:0], 3'b0};
    logic [31:0] load_data_fmt;
    always_comb begin
        logic [31:0] sh; sh = mem_word >> boff;
        unique case (f3)
            3'h0:    load_data_fmt = {{24{sh[7]}},  sh[7:0]};
            3'h1:    load_data_fmt = {{16{sh[15]}}, sh[15:0]};
            3'h4:    load_data_fmt = {24'b0, sh[7:0]};
            3'h5:    load_data_fmt = {16'b0, sh[15:0]};
            default: load_data_fmt = mem_word;
        endcase
    end

    // ---- writeback -------------------------------------------------------- //
    always_comb begin
        unique case (wb_sel)
            2'd0:    wb_data = compute;
            2'd1:    wb_data = load_data_fmt;
            2'd2:    wb_data = pc + 32'd4;
            default: wb_data = imm;
        endcase
    end
    assign wb_data_final = is_csr ? csr_old : wb_data;      // CSR reads land in rd

    // ---- branch / next PC ------------------------------------------------- //
    logic take_branch;
    always_comb begin
        unique case (f3)
            3'h0:    take_branch = (rdata1 == rdata2);
            3'h1:    take_branch = (rdata1 != rdata2);
            3'h4:    take_branch = ($signed(rdata1) <  $signed(rdata2));
            3'h5:    take_branch = ($signed(rdata1) >= $signed(rdata2));
            3'h6:    take_branch = (rdata1 <  rdata2);
            3'h7:    take_branch = (rdata1 >= rdata2);
            default: take_branch = 1'b0;
        endcase
    end
    logic [31:0] npc;
    always_comb begin
        if (do_enter)             npc = enter_target;
        else if (is_mret)         npc = ret_target;
        else if (jump)            npc = jalr ? ((rdata1 + imm) & ~32'd1) : (pc + imm);
        else if (branch && take_branch) npc = pc + imm;
        else                      npc = pc + 32'd4;
    end

    // ---- store byte-merge ------------------------------------------------- //
    logic [31:0] store_word;
    always_comb begin
        logic [31:0] cur; cur = wmem[alu_y[AW+1:2]];
        unique case (f3)
            3'h0:    store_word = cur & ~(32'hFF << boff)   | ((rdata2 & 32'hFF)   << boff);
            3'h1:    store_word = cur & ~(32'hFFFF << boff) | ((rdata2 & 32'hFFFF) << boff);
            default: store_word = rdata2;
        endcase
    end

    // ---- sequential state ------------------------------------------------- //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc <= 32'd0;
            mstatus_s<=0; mtvec_s<=0; mie_s<=0; mscratch_s<=0; mepc_s<=0; mcause_s<=0; mtval_s<=0;
        end else if (load_en) begin
            wmem[load_addr[AW+1:2]] <= load_data;
        end else begin
            pc <= npc;
            if (mem_write && !do_enter) wmem[alu_y[AW+1:2]] <= store_word;
            // CSR instruction store (WARL legalisation)
            if (csr_we && !take_int) begin
                case (funct12)
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
            // trap entry side-effects (mutually exclusive with csr_we)
            if (do_enter) begin
                mepc_s    <= enter_mepc;
                mcause_s  <= enter_mcause;
                mstatus_s <= enter_mstatus & MSTATUS_WMASK;
                mtval_s   <= take_int ? 32'd0 : (is_illegal ? ins : (is_ebreak ? pc : 32'd0));
            end
            // mret restores mstatus
            if (is_mret) mstatus_s <= ret_mstatus & MSTATUS_WMASK;
        end
    end
endmodule
