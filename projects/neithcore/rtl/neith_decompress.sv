// NeithCore — ML-KEM ciphertext Decompress_q — KemetCore Phase 2 RTL
//
// Decompress a d-bit compressed coefficient back to the ring Z_Q (Q=7681):
//   coeff = round(Q / 2^d * y) = (Q*y + 2^(d-1)) >> d        (round-half-up)
// Purely combinational — one constant multiply, a rounding add, and a shift; no
// divider. The result is always in [0, Q). Bit-exact vs golden neith_mlkem.decompress.

module neith_decompress #(
    parameter int D = 10                 // compression bit-width (Kyber du/dv)
) (
    input  logic [D-1:0]  y,             // compressed coefficient in [0, 2^d)
    output logic [12:0]   coeff          // decompressed coefficient in [0, Q)
);
    localparam int Q  = 7681;
    localparam int PW = 13 + D + 1;      // room for Q*y plus the rounding add

    wire [PW-1:0] num = (Q[PW-1:0] * {{(PW-D){1'b0}}, y}) + (PW'(1) << (D-1));
    assign coeff = num[D +: 13];         // (num >> D), which is < Q so fits 13 bits
endmodule
