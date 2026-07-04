// NeithCore — ML-KEM ciphertext Compress_q — KemetCore Phase 2 RTL
//
// Compress a ring coefficient x in [0, Q) (Q=7681) to d bits:
//   compress = round(2^d / Q * x) mod 2^d
//            = ( (x << d) + Q/2 ) / Q,  taken mod 2^d      (round-half-up)
// The divide is by the compile-time constant Q, which Yosys maps to a fixed
// reciprocal-multiply network (not a general divider); the numerator range is
// bounded (< Q*(2^d + 1)). Purely combinational. Bit-exact vs golden
// neith_mlkem.compress.

module neith_compress #(
    parameter int D = 10                 // compression bit-width (Kyber du/dv)
) (
    input  logic [12:0]  x,              // ring coefficient in [0, Q)
    output logic [D-1:0] c               // compressed coefficient in [0, 2^d)
);
    localparam int Q = 7681;

    // 32-bit clean datapath: numerator = (x << d) + Q/2, then divide by constant Q.
    wire [31:0] num  = ({19'd0, x} << D) + 32'(Q / 2);
    wire [31:0] quot = num / 32'(Q);
    // mod 2^d keeps only the low d bits of the quotient; the high bits are the
    // (discarded) integer part above 2^d and are intentionally unused.
    /* verilator lint_off UNUSEDSIGNAL */
    assign c = quot[D-1:0];
    /* verilator lint_on UNUSEDSIGNAL */
endmodule
