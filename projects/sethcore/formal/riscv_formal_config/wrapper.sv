module rvfi_wrapper (
    input         clock,
    input         reset,
    `RVFI_OUTPUTS
);
    wire halted;
    
    // Default unused signals to 0 to pass riscv-formal checks
    assign rvfi_csr_mstatus_rmask = 0;
    assign rvfi_csr_mstatus_wmask = 0;
    assign rvfi_csr_mstatus_rdata = 0;
    assign rvfi_csr_mstatus_wdata = 0;
    assign rvfi_csr_mie_rmask = 0;
    assign rvfi_csr_mie_wmask = 0;
    assign rvfi_csr_mie_rdata = 0;
    assign rvfi_csr_mie_wdata = 0;
    assign rvfi_csr_mtvec_rmask = 0;
    assign rvfi_csr_mtvec_wmask = 0;
    assign rvfi_csr_mtvec_rdata = 0;
    assign rvfi_csr_mtvec_wdata = 0;
    assign rvfi_csr_mscratch_rmask = 0;
    assign rvfi_csr_mscratch_wmask = 0;
    assign rvfi_csr_mscratch_rdata = 0;
    assign rvfi_csr_mscratch_wdata = 0;
    assign rvfi_csr_mepc_rmask = 0;
    assign rvfi_csr_mepc_wmask = 0;
    assign rvfi_csr_mepc_rdata = 0;
    assign rvfi_csr_mepc_wdata = 0;
    assign rvfi_csr_mcause_rmask = 0;
    assign rvfi_csr_mcause_wmask = 0;
    assign rvfi_csr_mcause_rdata = 0;
    assign rvfi_csr_mcause_wdata = 0;
    assign rvfi_csr_mtval_rmask = 0;
    assign rvfi_csr_mtval_wmask = 0;
    assign rvfi_csr_mtval_rdata = 0;
    assign rvfi_csr_mtval_wdata = 0;
    assign rvfi_csr_mip_rmask = 0;
    assign rvfi_csr_mip_wmask = 0;
    assign rvfi_csr_mip_rdata = 0;
    assign rvfi_csr_mip_wdata = 0;

    // Instantiate SethCore
    seth_pipeline_csr #(
        .WORDS(1024)
    ) dut (
        .clk        (clock),
        .rst        (reset),
        .load_en    (1'b0),
        .load_addr  (32'b0),
        .load_data  (32'b0),
        .irq_soft   (1'b0),
        .irq_timer  (1'b0),
        .irq_ext    (1'b0),
        .dbg_pc     (),
        .halted     (halted),
        `RVFI_CONN
    );
endmodule
