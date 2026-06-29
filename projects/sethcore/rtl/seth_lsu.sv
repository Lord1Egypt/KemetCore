// SethCore — load/store formatting unit (KemetCore Phase 2 RTL)
//
// Combinational byte/half/word formatting for a WORD-ADDRESSED data memory, the
// exact model seth_core uses inline. The memory delivers the aligned 32-bit word
// containing the access; this unit selects and extends the requested field using
// the low address bits.
//
// Load (funct3): lb/lh/lw/lbu/lhu. `shifted = mem_word >> (addr_lo*8)`, then the
// byte/half is sign- or zero-extended (lw passes the whole word).
//
// Store (funct3): sb/sh/sw. Read-modify-write merge of `store_data` (rs2) into the
// current word `mem_word` at the byte offset (sw replaces the word). The strobe
// `wstrb` (one bit per byte) is also exposed for memories that prefer byte-enables.
//
// Verified against the Python reference load_format / store_merge — see
// tb/test_lsu.py. Combinational only.

module seth_lsu (
    input  logic [2:0]  funct3,
    input  logic [1:0]  addr_lo,
    input  logic [31:0] mem_word,     // aligned word from memory
    input  logic [31:0] store_data,   // rs2 (store source)
    output logic [31:0] load_data,    // formatted load result
    output logic [31:0] store_word,   // word to write back (merged)
    output logic [3:0]  wstrb         // per-byte write strobe for the store
);
    wire [4:0]  boff    = {addr_lo, 3'b000};   // addr_lo * 8
    wire [31:0] shifted = mem_word >> boff;

    always_comb begin
        case (funct3)
            3'h0:    load_data = {{24{shifted[7]}},  shifted[7:0]};   // lb
            3'h1:    load_data = {{16{shifted[15]}}, shifted[15:0]};  // lh
            3'h2:    load_data = mem_word;                            // lw
            3'h4:    load_data = {24'b0, shifted[7:0]};               // lbu
            3'h5:    load_data = {16'b0, shifted[15:0]};              // lhu
            default: load_data = mem_word;
        endcase
    end

    always_comb begin
        case (funct3)
            3'h0: begin // sb
                store_word = (mem_word & ~(32'hFF   << boff)) | ((store_data & 32'hFF)   << boff);
                wstrb      = 4'b0001 << addr_lo;
            end
            3'h1: begin // sh
                store_word = (mem_word & ~(32'hFFFF << boff)) | ((store_data & 32'hFFFF) << boff);
                wstrb      = 4'b0011 << addr_lo;
            end
            default: begin // sw
                store_word = store_data;
                wstrb      = 4'b1111;
            end
        endcase
    end
endmodule
