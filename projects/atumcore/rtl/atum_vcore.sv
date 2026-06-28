// AtumCore — single-cycle vector core with vector memory (KemetCore Phase 2 RTL)
//
// Ties the verified vector blocks into a working processor, the way seth_core does
// for SethCore: a vector register file (atum_vregfile, 3 read ports), the vsetvl
// unit, the integrated execute unit (atum_vexec), and a word-addressable vector data
// memory with unit-stride load/store. One micro-instruction per cycle: fetch ->
// read vs1/vs2/vd (or memory) -> execute -> writeback. The testbench preloads the
// instruction memory, the data memory and the initial vector registers under reset,
// then runs to HALT and compares the whole machine state (vector register file +
// data memory) to a golden runner.
//
// Micro-instruction (32-bit):
//   [2:0]   kind   0=VSETVL, 1=VOP, 2=VHALT, 3=VLD, 4=VST
//   [7:3]   vd
//   [12:8]  vs1
//   [17:13] vs2
//   [19:18] vclass (VOP: 0=ALU, 1=FP, 2=RED)
//   [23:20] subop  (VOP: valu op / {3'b0,fop} / {3'b0,redop})
//   [31:24] imm8   (VSETVL: AVL; VLD/VST: base word index into data memory)
// VLD overwrites vd: element i = (i<vl) ? dmem[base+i] : 0  (matches golden load()).
// VST writes element i (i<vl) of vs1 to dmem[base+i]. All lanes execute unmasked;
// VL gates the body. Sequential state: vreg array, data memory, PC, VL, halt. 0-latch.

module atum_vcore #(
    parameter int NREGS  = 32,
    parameter int VLMAX  = 8,
    parameter int ELEN   = 32,
    parameter int IWORDS = 64,
    parameter int DWORDS = 256
) (
    input  logic                      clk,
    input  logic                      rst,
    input  logic                      load_imem,
    input  logic [$clog2(IWORDS)-1:0] load_iaddr,
    input  logic [31:0]               load_idata,
    input  logic                      load_dmem,
    input  logic [$clog2(DWORDS)-1:0] load_daddr,
    input  logic [31:0]               load_ddata,
    input  logic                      load_vreg,
    input  logic [$clog2(NREGS)-1:0]  load_vaddr,
    input  logic [VLMAX*ELEN-1:0]     load_vdata,
    output logic [$clog2(IWORDS)-1:0] dbg_pc,
    output logic                      halted
);
    localparam int VLEN = VLMAX * ELEN;
    localparam int VLW  = $clog2(VLMAX+1);
    localparam int RW   = $clog2(NREGS);
    localparam int PW   = $clog2(IWORDS);
    localparam int DW   = $clog2(DWORDS);

    localparam logic [2:0] K_VSETVL = 3'd0, K_VOP = 3'd1, K_VHALT = 3'd2,
                           K_VLD = 3'd3, K_VST = 3'd4;

    logic [31:0]    imem [0:IWORDS-1];
    logic [31:0]    dmem [0:DWORDS-1];
    logic [PW-1:0]  pc;
    logic [VLW-1:0] vl;
    assign dbg_pc = pc;

    // -------- fetch + decode -------- //
    logic [31:0]   ins;
    logic [2:0]    kind;
    logic [1:0]    vclass;
    logic [RW-1:0] vd, vs1, vs2;
    logic [3:0]    subop;
    logic [7:0]    imm8;
    assign ins    = imem[pc];
    assign kind   = ins[2:0];
    assign vd     = ins[3  +: RW];
    assign vs1    = ins[8  +: RW];
    assign vs2    = ins[13 +: RW];
    assign vclass = ins[19:18];
    assign subop  = ins[23:20];
    assign imm8   = ins[31:24];

    logic running;
    assign running = ~halted & ~rst & ~load_imem & ~load_dmem & ~load_vreg;

    // -------- register file (3 read ports); write port muxed: preload / VLD / VOP -- //
    logic [VLEN-1:0] rd1, rd2, rdvd, vexec_out, vld_vec;
    logic            rf_we;
    logic [RW-1:0]   rf_waddr;
    logic [VLEN-1:0] rf_wdata;
    assign rf_we    = load_vreg ? 1'b1
                    : (running & (kind == K_VOP | kind == K_VLD));
    assign rf_waddr = load_vreg ? load_vaddr : vd;
    assign rf_wdata = load_vreg ? load_vdata
                    : (kind == K_VLD) ? vld_vec : vexec_out;

    atum_vregfile #(.NREGS(NREGS), .VLMAX(VLMAX), .ELEN(ELEN)) u_rf (
        .clk(clk), .rst(rst), .we(rf_we), .waddr(rf_waddr), .wdata(rf_wdata),
        .raddr1(vs1), .raddr2(vs2), .raddr3(vd),
        .rdata1(rd1), .rdata2(rd2), .rdata3(rdvd));

    // -------- vsetvl + execute -------- //
    logic [VLW-1:0] vl_new;
    atum_vsetvl #(.VLMAX(VLMAX)) u_vsetvl (.avl({24'b0, imm8}), .vl(vl_new));

    atum_vexec #(.VLMAX(VLMAX), .ELEN(ELEN)) u_vexec (
        .vs1(rd1), .vs2(rd2), .vd_old(rdvd),
        .vclass(vclass), .subop(subop),
        .mask({VLMAX{1'b1}}), .vl(vl), .vd_new(vexec_out));

    // -------- VLD: gather VLMAX unit-stride words from dmem (element i<vl else 0) -- //
    always_comb begin
        logic [DW-1:0] idx;
        for (int i = 0; i < VLMAX; i++) begin
            idx = DW'(imm8) + DW'(i);
            vld_vec[i*ELEN +: ELEN] = (VLW'(i) < vl) ? dmem[idx] : '0;
        end
    end

    // -------- sequential -------- //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc <= '0; vl <= VLW'(VLMAX); halted <= 1'b0;
        end else if (load_imem) begin
            imem[load_iaddr] <= load_idata;
        end else if (load_dmem) begin
            dmem[load_daddr] <= load_ddata;
        end else if (load_vreg) begin
            ;  // vreg preload commits through the regfile write port (rf_we)
        end else if (!halted) begin
            if (kind == K_VHALT) begin
                halted <= 1'b1;
            end else begin
                if (kind == K_VSETVL) vl <= vl_new;
                if (kind == K_VST) begin
                    for (int i = 0; i < VLMAX; i++)
                        if (VLW'(i) < vl)
                            dmem[DW'(imm8) + DW'(i)] <= rd1[i*ELEN +: ELEN];
                end
                pc <= pc + PW'(1);
            end
        end
    end
endmodule
