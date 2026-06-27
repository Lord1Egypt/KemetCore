// SethCore — single-cycle RV32IM core (KemetCore Phase 2 RTL)
//
// The first integrated datapath: wires together the verified building blocks
// (seth_decode, seth_imm, seth_aluctl, seth_alu, seth_muldiv, seth_regfile) plus
// instruction fetch, a word-addressed memory, branch/jump control flow and
// writeback. One instruction completes per clock — no pipeline, hence no hazards
// (a clean functional baseline; the pipelined version is built on top later).
//
// Memory is internal and word-addressed (WORDS x 32b). The testbench preloads the
// program/data via the load_* port while rst is asserted, then runs the core until
// `halted` (set by a system instruction, opcode 0x73). Registers are inspected
// hierarchically (rf.regs). Verified by running the golden's programs and comparing
// final architectural state — see tb/test_core.py.

module seth_core #(
    parameter int WORDS = 1024              // 4 KiB word-addressed memory
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        load_en,            // preload: write load_data @ load_addr
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    output logic [31:0] dbg_pc,
    output logic        halted
);
    localparam int AW = $clog2(WORDS);

    logic [31:0] wmem [0:WORDS-1];
    logic [31:0] pc;
    assign dbg_pc = pc;

    // ---- fetch ------------------------------------------------------------ //
    logic [31:0] ins;
    assign ins = wmem[pc[AW+1:2]];

    logic [4:0]  rs1, rs2, rd;
    logic [2:0]  f3;
    logic [6:0]  op;
    assign op  = ins[6:0];
    assign rs1 = ins[19:15];
    assign rs2 = ins[24:20];
    assign rd  = ins[11:7];
    assign f3  = ins[14:12];

    // ---- decode + control ------------------------------------------------- //
    logic reg_write, alu_src_imm, a_src_pc, mem_read, mem_write, branch, jump, jalr, is_mdu;
    logic [1:0] wb_sel;
    seth_decode u_dec (
        .ins(ins), .reg_write(reg_write), .alu_src_imm(alu_src_imm), .a_src_pc(a_src_pc),
        .mem_read(mem_read), .mem_write(mem_write), .branch(branch), .jump(jump),
        .jalr(jalr), .is_mdu(is_mdu), .wb_sel(wb_sel));

    logic [31:0] imm;
    seth_imm u_imm (.ins(ins), .imm(imm));

    logic [3:0] alu_op;
    seth_aluctl u_actl (.opcode(op), .funct3(f3), .funct7(ins[31:25]), .alu_op(alu_op));

    // ---- register read ---------------------------------------------------- //
    logic [31:0] rdata1, rdata2, wb_data;
    seth_regfile u_rf (
        .clk(clk), .rst(rst), .we(reg_write & ~halted & ~load_en), .waddr(rd), .wdata(wb_data),
        .raddr1(rs1), .raddr2(rs2), .rdata1(rdata1), .rdata2(rdata2));

    // ---- execute ---------------------------------------------------------- //
    logic [31:0] alu_a, alu_b, alu_y, mdu_y, compute;
    assign alu_a = a_src_pc ? pc : rdata1;
    assign alu_b = alu_src_imm ? imm : rdata2;
    seth_alu     u_alu (.a(alu_a), .b(alu_b), .op(alu_op), .y(alu_y));
    seth_muldiv  u_mdu (.a(rdata1), .b(rdata2), .op(f3), .y(mdu_y));
    assign compute = is_mdu ? mdu_y : alu_y;

    // ---- load formatting (word-addressed memory, byte/half via offset) ----- //
    logic [31:0] mem_word, load_data_fmt;
    logic [4:0]  boff;                                   // bit offset = addr[1:0]*8
    assign mem_word = wmem[alu_y[AW+1:2]];
    assign boff     = {alu_y[1:0], 3'b0};
    always_comb begin
        logic [31:0] shifted;
        shifted = mem_word >> boff;
        unique case (f3)
            3'h0:    load_data_fmt = {{24{shifted[7]}},  shifted[7:0]};    // lb
            3'h1:    load_data_fmt = {{16{shifted[15]}}, shifted[15:0]};   // lh
            3'h2:    load_data_fmt = mem_word;                            // lw
            3'h4:    load_data_fmt = {24'b0, shifted[7:0]};               // lbu
            3'h5:    load_data_fmt = {16'b0, shifted[15:0]};              // lhu
            default: load_data_fmt = mem_word;
        endcase
    end

    // ---- writeback select ------------------------------------------------- //
    always_comb begin
        unique case (wb_sel)
            2'd0:    wb_data = compute;                  // ALU / MDU
            2'd1:    wb_data = load_data_fmt;            // load
            2'd2:    wb_data = pc + 32'd4;               // link (jal/jalr)
            default: wb_data = imm;                      // LUI
        endcase
    end

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
        if (jump)
            npc = jalr ? ((rdata1 + imm) & ~32'd1) : (pc + imm);
        else if (branch && take_branch)
            npc = pc + imm;
        else
            npc = pc + 32'd4;
    end

    logic is_system;
    assign is_system = (op == 7'h73);

    // ---- store byte-merge ------------------------------------------------- //
    logic [31:0] store_word;
    always_comb begin
        logic [31:0] cur;
        cur = wmem[alu_y[AW+1:2]];
        unique case (f3)
            3'h0:    store_word = cur & ~(32'hFF << boff)   | ((rdata2 & 32'hFF)   << boff);  // sb
            3'h1:    store_word = cur & ~(32'hFFFF << boff) | ((rdata2 & 32'hFFFF) << boff);  // sh
            default: store_word = rdata2;                                                     // sw
        endcase
    end

    // ---- sequential state ------------------------------------------------- //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc     <= 32'd0;
            halted <= 1'b0;
        end else if (load_en) begin
            wmem[load_addr[AW+1:2]] <= load_data;
        end else if (!halted) begin
            pc <= npc;
            if (is_system)
                halted <= 1'b1;
            if (mem_write)
                wmem[alu_y[AW+1:2]] <= store_word;
        end
    end
endmodule
