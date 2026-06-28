// AtumCore — single-cycle vector core (KemetCore Phase 2 RTL)
//
// Ties the verified vector blocks into a working processor, the way seth_core does
// for SethCore: a vector register file (atum_vregfile, 3 read ports), the vsetvl
// unit, and the integrated execute unit (atum_vexec). One micro-instruction per
// cycle: fetch -> read vs1/vs2/vd -> execute -> writeback. The testbench preloads the
// instruction memory and the initial vector registers under reset, then runs to a
// HALT and compares the whole vector register file to a golden runner.
//
// Micro-instruction (32-bit):
//   [1:0]   kind   0=VSETVL, 1=VOP, 2=VHALT
//   [6:2]   vd
//   [11:7]  vs1
//   [16:12] vs2
//   [18:17] vclass (VOP: 0=ALU, 1=FP, 2=RED)
//   [22:19] subop  (VOP: valu op / {3'b0,fop} / {3'b0,redop})
//   [31:23] avl    (VSETVL: application vector length, 0..256)
// All lanes execute unmasked (mask = all ones); VL gates the body. Sequential state
// is the vreg array, PC, VL and the halt flag. Yosys 0-latch.

module atum_vcore #(
    parameter int NREGS  = 32,
    parameter int VLMAX  = 8,
    parameter int ELEN   = 32,
    parameter int IWORDS = 64
) (
    input  logic                      clk,
    input  logic                      rst,
    input  logic                      load_imem,
    input  logic [$clog2(IWORDS)-1:0] load_iaddr,
    input  logic [31:0]               load_idata,
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

    localparam logic [1:0] K_VSETVL = 2'd0, K_VOP = 2'd1, K_VHALT = 2'd2;

    logic [31:0]    imem [0:IWORDS-1];
    logic [PW-1:0]  pc;
    logic [VLW-1:0] vl;
    assign dbg_pc = pc;

    // -------- fetch + decode -------- //
    logic [31:0]   ins;
    logic [1:0]    kind, vclass;
    logic [RW-1:0] vd, vs1, vs2;
    logic [3:0]    subop;
    logic [8:0]    avl;
    assign ins    = imem[pc];
    assign kind   = ins[1:0];
    assign vd     = ins[2  +: RW];
    assign vs1    = ins[7  +: RW];
    assign vs2    = ins[12 +: RW];
    assign vclass = ins[18:17];
    assign subop  = ins[22:19];
    assign avl    = ins[31:23];

    // -------- register file (3 read ports: vs1, vs2, vd); write port muxed with preload -------- //
    logic [VLEN-1:0] rd1, rd2, rdvd, vexec_out;
    logic            wr_en, rf_we;
    logic [RW-1:0]   rf_waddr;
    logic [VLEN-1:0] rf_wdata;
    assign wr_en    = ~halted & ~rst & ~load_imem & ~load_vreg & (kind == K_VOP);
    assign rf_we    = load_vreg ? 1'b1        : wr_en;
    assign rf_waddr = load_vreg ? load_vaddr  : vd;
    assign rf_wdata = load_vreg ? load_vdata  : vexec_out;

    atum_vregfile #(.NREGS(NREGS), .VLMAX(VLMAX), .ELEN(ELEN)) u_rf (
        .clk(clk), .rst(rst), .we(rf_we), .waddr(rf_waddr), .wdata(rf_wdata),
        .raddr1(vs1), .raddr2(vs2), .raddr3(vd),
        .rdata1(rd1), .rdata2(rd2), .rdata3(rdvd));

    // -------- vsetvl + execute -------- //
    logic [VLW-1:0] vl_new;
    atum_vsetvl #(.VLMAX(VLMAX)) u_vsetvl (.avl({23'b0, avl}), .vl(vl_new));

    atum_vexec #(.VLMAX(VLMAX), .ELEN(ELEN)) u_vexec (
        .vs1(rd1), .vs2(rd2), .vd_old(rdvd),
        .vclass(vclass), .subop(subop),
        .mask({VLMAX{1'b1}}), .vl(vl), .vd_new(vexec_out));

    // -------- sequential (pc / vl / halt / imem) -------- //
    always_ff @(posedge clk) begin
        if (rst) begin
            pc <= '0; vl <= VLW'(VLMAX); halted <= 1'b0;
        end else if (load_imem) begin
            imem[load_iaddr] <= load_idata;
        end else if (load_vreg) begin
            ;  // vreg preload commits through the regfile write port (rf_we)
        end else if (!halted) begin
            if (kind == K_VHALT) begin
                halted <= 1'b1;
            end else begin
                if (kind == K_VSETVL) vl <= vl_new;
                pc <= pc + PW'(1);
            end
        end
    end
endmodule
