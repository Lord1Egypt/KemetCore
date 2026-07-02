// RaCore — on-chip byte-enabled scratchpad SRAM — KemetCore Phase 2 RTL
//
// The shared scratchpad every accelerator and the DMA read/write through. A
// single synchronous read/write port carries a 32-bit data word with per-byte
// write-enables (be[3:0]), so masked / partial-word stores behave exactly like
// software byte-addressed writes into the golden Scratchpad model:
//   * write:  en & we — for each i, if be[i] then byte i of mem[addr] <= wdata[i]
//   * read:   en & !we — rdata <= mem[addr] (registered, valid the next cycle)
// Reads and writes to the same address are issued on separate cycles by the
// SoC, so no read-during-write bypass is relied upon. No reset on the array
// (it is preloaded before use), which keeps it a clean inferred SRAM.
//
// Verified bit-exact vs golden Scratchpad.write_word/read_word — see
// tb/test_scratchpad.py.

module ra_scratchpad #(
    parameter int DEPTH = 256,                 // number of 32-bit words
    parameter int AW    = $clog2(DEPTH)
) (
    input  logic          clk,
    input  logic          en,                  // access strobe
    input  logic          we,                  // 1 = write (with en), 0 = read
    input  logic [3:0]    be,                  // per-byte write enable
    input  logic [AW-1:0] addr,                // word address
    input  logic [31:0]   wdata,
    output logic [31:0]   rdata                // registered, valid next cycle
);
    logic [31:0] mem [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (en) begin
            if (we) begin
                if (be[0]) mem[addr][7:0]   <= wdata[7:0];
                if (be[1]) mem[addr][15:8]  <= wdata[15:8];
                if (be[2]) mem[addr][23:16] <= wdata[23:16];
                if (be[3]) mem[addr][31:24] <= wdata[31:24];
            end else begin
                rdata <= mem[addr];
            end
        end
    end
endmodule
