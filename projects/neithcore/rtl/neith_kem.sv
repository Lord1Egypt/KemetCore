// NeithCore — ML-KEM Top-Level Integration (KemetCore Phase 2 RTL)
//
// This module provides the capstone integration for NeithCore.
// It wraps the verified neith_ntt engine into a top-level macro.
// Full Kyber keygen/encaps/decaps FSMs require integrating AnubisCore hashes
// which is a Phase 3/4 activity, but this module stands as the structural
// top-level for the accelerator.

module neith_kem (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic        mode, // 0 = forward, 1 = inverse
    output logic        done,
    
    // Memory interface
    output logic        mem_we,
    output logic [7:0]  mem_addr,
    output logic [12:0] mem_wdata,
    input  logic [12:0] mem_rdata
);

    // Instantiate the verified NTT engine
    logic        ntt_start;
    logic        ntt_mode;
    logic        ntt_nega;
    logic        ntt_done;
    logic        ntt_mem_we;
    logic [7:0]  ntt_mem_addr;
    logic [12:0] ntt_mem_wdata;
    
    assign ntt_start = start;
    assign ntt_mode = mode;
    assign ntt_nega = 1'b1; // ML-KEM uses negacyclic

    neith_ntt u_ntt (
        .clk(clk),
        .rst_n(rst_n),
        .start(ntt_start),
        .mode(ntt_mode),
        .nega(ntt_nega),
        .din(mem_rdata),       // In a full integration, din is streamed from memory
        .we(ntt_mem_we),
        .waddr(ntt_mem_addr),
        .dout(ntt_mem_wdata),
        .done(ntt_done)
    );

    assign mem_we = ntt_mem_we;
    assign mem_addr = ntt_mem_addr;
    assign mem_wdata = ntt_mem_wdata;
    assign done = ntt_done;

endmodule
