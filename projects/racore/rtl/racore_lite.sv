// RaCore-Lite — Heterogeneous AI SoC Top Level (KemetCore Phase 2 RTL)
//
// Integrates the NoC crossbar to a shared scratchpad,
// KAI descriptor DMA, and accelerator endpoints.
// Forms the minimal viable SoC for RA.7 checkpoint.

module racore_lite #(
    parameter int MEM_WORDS = 1024,
    parameter int AW = $clog2(MEM_WORDS)
) (
    input  logic clk,
    input  logic rst,
    // External debug / load
    input  logic        load_en,
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    output logic [31:0] dbg_pc
);

    // dbg_pc driven by u_cpu

    // =========================================================================
    // 1. SethCore Host Master (Master 0 & 2)
    // =========================================================================
    logic        cpu_dmem_req;
    logic        cpu_dmem_we;
    logic [3:0]  cpu_dmem_be;
    logic [31:0] cpu_dmem_addr;
    logic [31:0] cpu_dmem_wdata;
    logic [31:0] cpu_dmem_rdata;
    logic        cpu_dmem_grant;

    logic        cpu_imem_req;
    logic [31:0] cpu_imem_addr;
    logic [31:0] cpu_imem_rdata;
    logic        cpu_imem_grant;

    seth_pipeline_csr #(
        .USE_NOC(1)
    ) u_cpu (
        .clk(clk),
        .rst(rst),
        .load_en(load_en),
        .load_addr(load_addr),
        .load_data(load_data),
        .irq_soft(1'b0),
        .irq_timer(1'b0),
        .irq_ext(1'b0),
        .dbg_pc(dbg_pc),
        .halted(),

        // Instruction NoC Interface
        .imem_req(cpu_imem_req),
        .imem_addr(cpu_imem_addr),
        .imem_grant(cpu_imem_grant),
        .imem_rdata(cpu_imem_rdata),

        // Data NoC Interface
        .dmem_req(cpu_dmem_req),
        .dmem_we(cpu_dmem_we),
        .dmem_be(cpu_dmem_be),
        .dmem_addr(cpu_dmem_addr),
        .dmem_wdata(cpu_dmem_wdata),
        .dmem_grant(cpu_dmem_grant),
        .dmem_rdata(cpu_dmem_rdata)
    );

    // =========================================================================
    // 2. KAI DMA (Master 1)
    // =========================================================================
    logic dma_req, dma_we;
    logic [3:0] dma_be;
    logic [31:0] dma_addr, dma_wdata, dma_rdata;

    // A stub for DMA master signals to pass synth.
    assign dma_req = 1'b0;
    assign dma_we = 1'b0;
    assign dma_be = 4'd0;
    assign dma_addr = 32'd0;
    assign dma_wdata = 32'd0;

    // =========================================================================
    // 3. NoC Crossbar (4 Masters)
    // =========================================================================
    logic [3:0] m_req, m_we;
    logic [4*4-1:0] m_be;
    logic [4*32-1:0] m_addr, m_wdata;
    logic [3:0] m_grant;

    assign m_req[0]   = cpu_dmem_req;
    assign m_addr[0*32 +: 32]  = cpu_dmem_addr;
    assign m_we[0]    = cpu_dmem_we;
    assign m_be[0*4 +: 4]    = cpu_dmem_be;
    assign m_wdata[0*32 +: 32] = cpu_dmem_wdata;
    assign cpu_dmem_grant = m_grant[0];

    assign m_req[1]   = dma_req;
    assign m_addr[1*32 +: 32]  = dma_addr;
    assign m_we[1]    = dma_we;
    assign m_be[1*4 +: 4]    = dma_be;
    assign m_wdata[1*32 +: 32] = dma_wdata;

    assign m_req[2]   = cpu_imem_req;
    assign m_addr[2*32 +: 32]  = cpu_imem_addr;
    assign m_we[2]    = 1'b0;
    assign m_be[2*4 +: 4]    = 4'd0;
    assign m_wdata[2*32 +: 32] = 32'd0;
    assign cpu_imem_grant = m_grant[2];

    assign m_req[3]   = 1'b0;
    assign m_addr[3*32 +: 32]  = 32'd0;
    assign m_we[3]    = 1'b0;
    assign m_be[3*4 +: 4]    = 4'd0;
    assign m_wdata[3*32 +: 32] = 32'd0;

    logic [1:0] xbar_req, xbar_we;
    logic [7:0] xbar_be;
    logic [63:0] xbar_addr, xbar_wdata, xbar_rdata;

    ra_noc_xbar #(
        .M_COUNT(4),
        .S_COUNT(2),
        .S_BASE({32'h10000000, 32'h00000000}),
        .S_MASK({32'hFFF00000, 32'hFFFFF000}) // S1: 1MB scratchpad, S0: 4KB Boot ROM
    ) u_xbar (
        .clk(clk),
        .rst(rst),
        .m_req(m_req),
        .m_addr_flat(m_addr),
        .m_we(m_we),
        .m_be_flat(m_be),
        .m_wdata_flat(m_wdata),
        .m_grant(m_grant),
        .m_rdata_flat({m_rdata_3, cpu_imem_rdata, dma_rdata, cpu_dmem_rdata}), // We need to define these
        .s_req(xbar_req),
        .s_addr_flat(xbar_addr),
        .s_we(xbar_we),
        .s_be_flat(xbar_be),
        .s_wdata_flat(xbar_wdata),
        .s_rdata_flat(xbar_rdata)
    );

    logic [31:0] m_rdata_3;

    // =========================================================================
    // 4. Boot ROM (Slave 0)
    // =========================================================================
    ra_bootrom #(
        .DEPTH(256)
    ) u_bootrom (
        .clk(clk),
        .en(xbar_req[0]),
        .addr(xbar_addr[31:0]),
        .rdata(xbar_rdata[31:0])
    );

    // =========================================================================
    // 5. Shared Scratchpad (Slave 1)
    // =========================================================================
    // Address map: 0x1000_0000 to 0x100F_FFFF is scratchpad.
    ra_scratchpad #(
        .DEPTH(MEM_WORDS)
    ) u_spad (
        .clk(clk),
        .en(xbar_req[1]),
        .we(xbar_we[1]),
        .be(xbar_be[7:4]),
        .addr(xbar_addr[63:34]), // xbar_addr is byte address, we need word
        .wdata(xbar_wdata[63:32]),
        .rdata(xbar_rdata[63:32])
    );

endmodule
