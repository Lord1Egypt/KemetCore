// RaCore — KAI-compliant DMA accelerator (KemetCore Phase 2 RTL)
//
// The first end-to-end KAI device: it wraps the verified ra_dma 1D copy engine in
// the ra_kai_regs MMIO contract, so the host drives it exactly like any other
// accelerator -- program SRC/DST/LEN, write CTRL.GO, poll STATUS.DONE, read PERF.
// Writing CTRL.GO launches a copy of LEN bytes from SRC to DST through the
// scratchpad; a cycle counter times the transfer and is latched into PERF when the
// engine signals done (which also sets STATUS.DONE).
//
// Verified end-to-end vs golden Dma + KaiRegs — see tb/test_kai_dma.py.

module ra_kai_dma #(
    parameter logic [7:0] BLOCK_ID = 8'h0D,   // 'D' for DMA
    parameter int         AW       = 10
) (
    input  logic          clk,
    input  logic          rst,
    // KAI MMIO
    input  logic [11:0]   addr,
    input  logic          wen,
    input  logic          ren,
    input  logic [31:0]   wdata,
    output logic [31:0]   rdata,
    // scratchpad preload / readback
    input  logic          load_en,
    input  logic [AW-1:0] load_addr,
    input  logic [7:0]    load_data,
    input  logic [AW-1:0] rd_addr,
    output logic [7:0]    rd_data
);
    // --- KAI register block ------------------------------------------------ //
    logic        go, dma_busy, dma_done;
    logic [31:0] src, dst, len, ctrl, perf;

    ra_kai_regs #(.BLOCK_ID(BLOCK_ID)) u_regs (
        .clk(clk), .rst(rst), .addr(addr), .wen(wen), .ren(ren), .wdata(wdata),
        .rdata(rdata), .go(go), .done(dma_done), .err_in(1'b0), .perf(perf),
        .src(src), .dst(dst), .len(len), .ctrl(ctrl)
    );

    // --- elapsed-cycle counter (GO .. done) -------------------------------- //
    always_ff @(posedge clk) begin
        if (rst)        perf <= 32'd0;
        else if (go)    perf <= 32'd1;          // count the launch cycle
        else if (dma_busy) perf <= perf + 32'd1;
    end

    // --- DMA engine (1D: rows=1, row_bytes=LEN) ---------------------------- //
    ra_dma #(.AW(AW)) u_dma (
        .clk(clk), .rst(rst),
        .load_en(load_en), .load_addr(load_addr), .load_data(load_data),
        .rd_addr(rd_addr), .rd_data(rd_data),
        .src(src[AW-1:0]), .dst(dst[AW-1:0]),
        .rows(16'd1), .row_bytes(len[15:0]),
        .src_stride(len[15:0]), .dst_stride(len[15:0]),
        .start(go), .busy(dma_busy), .done(dma_done)
    );
endmodule
