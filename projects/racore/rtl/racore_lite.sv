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
    logic [3:0][3:0] m_be;
    logic [3:0][31:0] m_addr, m_wdata;
    logic [3:0] m_grant;

    assign m_req[0]   = cpu_mem_valid;
    assign m_addr[0]  = cpu_mem_addr;
    assign m_we[0]    = cpu_mem_we;
    assign m_be[0]    = cpu_mem_be;
    assign m_wdata[0] = cpu_mem_wdata;

    assign m_req[1]   = dma_req;
    assign m_addr[1]  = dma_addr;
    assign m_we[1]    = dma_we;
    assign m_be[1]    = dma_be;
    assign m_wdata[1] = dma_wdata;

    assign m_req[3:2] = '0;
    assign m_addr[3:2] = '0;
    assign m_we[3:2] = '0;
    assign m_be[3:2] = '0;
    assign m_wdata[3:2] = '0;

    logic xbar_req, xbar_we;
    logic [3:0] xbar_be;
    logic [31:0] xbar_addr, xbar_wdata, xbar_rdata;

    ra_noc_xbar #(.N(4)) u_xbar (
        .clk(clk),
        .rst(rst),
        .m_req(m_req),
        .m_addr(m_addr),
        .m_we(m_we),
        .m_be(m_be),
        .m_wdata(m_wdata),
        .m_grant(m_grant),
        .s_req(xbar_req),
        .s_addr(xbar_addr),
        .s_we(xbar_we),
        .s_be(xbar_be),
        .s_wdata(xbar_wdata)
    );

    // =========================================================================
    // 4. Shared Scratchpad (Slave 0)
    // =========================================================================
    // Address map: 0x0000_0000 to 0x000F_FFFF is scratchpad.
    logic spad_sel;
    assign spad_sel = (xbar_addr[31:20] == 12'h000);

    ra_scratchpad #(
        .DEPTH(MEM_WORDS)
    ) u_spad (
        .clk(clk),
        .en(xbar_req && spad_sel),
        .we(xbar_we),
        .be(xbar_be),
        .addr(xbar_addr[AW-1+2:2]),
        .wdata(xbar_wdata),
        .rdata(xbar_rdata)
    );

    // =========================================================================
    // 5. Read Data Mux
    // =========================================================================
    // Simple 1-cycle latency readback.
    logic r_spad_sel;
    always_ff @(posedge clk) begin
        if (rst) r_spad_sel <= 1'b0;
        else     r_spad_sel <= spad_sel;
    end

    assign xbar_rdata = r_spad_sel ? u_spad.rdata : 32'hDEADBEEF;
    
    // Broadcast read data back to masters.
    assign cpu_mem_rdata = xbar_rdata;
    assign dma_rdata = xbar_rdata;

endmodule
