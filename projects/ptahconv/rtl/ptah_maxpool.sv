// PtahConv — fp32 2x2 max-pooling — KemetCore Phase 2 RTL
//
// Return the maximum of a 2x2 window of four fp32 lanes by IEEE total order:
// the monotonic key k = x ^ (x[31] ? 0xFFFFFFFF : 0x80000000) makes an unsigned
// compare equal the real ordering (-0 just below +0), so a max tree of pairwise
// key-compares needs no arithmetic comparator. Plain total-order max (no fmin/fmax
// NaN special-casing). Purely combinational. Bit-exact vs golden maxpool2x2.

module ptah_maxpool (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    input  logic [31:0] d,
    output logic [31:0] y
);
    function automatic logic [31:0] okey(input logic [31:0] x);
        okey = x ^ (x[31] ? 32'hFFFF_FFFF : 32'h8000_0000);
    endfunction

    wire [31:0] ab = (okey(a) >= okey(b)) ? a : b;
    wire [31:0] cd = (okey(c) >= okey(d)) ? c : d;
    assign y = (okey(ab) >= okey(cd)) ? ab : cd;
endmodule
