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

    assign dbg_pc = 32'd0;

    // =========================================================================
    // 1. Host Master Stub (Master 0)
    // =========================================================================
    logic        cpu_mem_valid;
    logic        cpu_mem_we;
    logic [3:0]  cpu_mem_be;
    logic [31:0] cpu_mem_addr;
    logic [31:0] cpu_mem_wdata;
    logic [31:0] cpu_mem_rdata;

    assign cpu_mem_valid = 1'b0;
    assign cpu_mem_we = 1'b0;
    assign cpu_mem_be = 4'd0;
    assign cpu_mem_addr = 32'd0;
    assign cpu_mem_wdata = 32'd0;

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

    assign m_req[0]   = cpu_mem_valid;
    assign m_addr[0*32 +: 32]  = cpu_mem_addr;
    assign m_we[0]    = cpu_mem_we;
    assign m_be[0*4 +: 4]    = cpu_mem_be;
    assign m_wdata[0*32 +: 32] = cpu_mem_wdata;

    assign m_req[1]   = dma_req;
    assign m_addr[1*32 +: 32]  = dma_addr;
    assign m_we[1]    = dma_we;
    assign m_be[1*4 +: 4]    = dma_be;
    assign m_wdata[1*32 +: 32] = dma_wdata;

    assign m_req[3:2] = '0;
    assign m_addr[4*32-1:2*32] = '0;
    assign m_we[3:2] = '0;
    assign m_be[4*4-1:2*4] = '0;
    assign m_wdata[4*32-1:2*32] = '0;

    logic [0:0] xbar_req, xbar_we;
    logic [3:0] xbar_be;
    logic [31:0] xbar_addr, xbar_wdata, xbar_rdata;

    ra_noc_xbar #(
        .M_COUNT(4),
        .S_COUNT(1),
        .S_BASE({32'h00000000}),
        .S_MASK({32'hFFF00000}) // 1MB scratchpad space
    ) u_xbar (
        .clk(clk),
        .rst(rst),
        .m_req(m_req),
        .m_addr_flat(m_addr),
        .m_we(m_we),
        .m_be_flat(m_be),
        .m_wdata_flat(m_wdata),
        .m_grant(m_grant),
        .m_rdata_flat({m_rdata_3, m_rdata_2, dma_rdata, cpu_mem_rdata}), // We need to define these
        .s_req(xbar_req),
        .s_addr_flat(xbar_addr),
        .s_we(xbar_we),
        .s_be_flat(xbar_be),
        .s_wdata_flat(xbar_wdata),
        .s_rdata_flat(xbar_rdata)
    );

    logic [31:0] m_rdata_2, m_rdata_3;

    // =========================================================================
    // 4. Shared Scratchpad (Slave 0)
    // =========================================================================
    // Address map: 0x0000_0000 to 0x000F_FFFF is scratchpad.
    ra_scratchpad #(
        .DEPTH(MEM_WORDS)
    ) u_spad (
        .clk(clk),
        .en(xbar_req[0]),
        .we(xbar_we[0]),
        .be(xbar_be),
        .addr(xbar_addr[AW-1+2:2]),
        .wdata(xbar_wdata),
        .rdata(xbar_rdata)
    );

endmodule
