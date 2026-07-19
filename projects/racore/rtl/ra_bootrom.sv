// RaCore Boot ROM
//
// A simple Read-Only Memory that holds the initial boot instructions for SethCore.
// Mapped into the NoC crossbar (typically at an address like 0x80000000 or similar,
// but for RaCore we can map it to 0x00000000 and move the scratchpad).

module ra_bootrom #(
    parameter int DEPTH = 256
) (
    input  logic clk,
    input  logic en,
    input  logic [31:0] addr, // word address
    output logic [31:0] rdata
);

    // The actual ROM contents
    logic [31:0] rom [0:DEPTH-1];

    initial begin
        // For now, an infinite loop to halt the CPU if it executes uninitialized memory
        for (int i = 0; i < DEPTH; i++) begin
            rom[i] = 32'h0000006F; // j 0
        end
        
        $readmemh("../tests/firmware/bootrom.hex", rom);
    end

    always_ff @(posedge clk) begin
        if (en) begin
            if (addr < DEPTH) begin
                rdata <= rom[addr];
            end else begin
                rdata <= 32'h00000000;
            end
        end
    end

endmodule
