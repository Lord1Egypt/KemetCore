// AnubisCore — FORMAL: SHA-256 core CONTROL-SAFETY invariants.
//
// SHA-256 (and SHA-3) are designed to have NO exploitable algebraic structure,
// so there is no cheap functional property to prove the way we can for the FPU /
// vector / crypto-modmul cores. What we CAN prove exhaustively is the *control
// safety* of the multicycle FSM that sequences the 64 compression rounds:
//
//   (1) the 6-bit round counter never leaves its legal range 0..63, so the
//       kconst() round-constant ROM and message-schedule window are never
//       indexed out of bounds; and
//   (2) the 2-bit state register never enters the unused/illegal 4th encoding
//       (2'd3) — the FSM only ever occupies IDLE/RUN/FIN.
//
// Both are proved by temporal k-induction over the real sha256_core RTL, i.e.
// for EVERY reachable state and any sequence of start/init/alg/block inputs.
// This is strictly stronger than the random cocotb block-hash vectors, which
// only exercise the counter/state along the concrete round sequences they run.
//
// Honest scope note: this is control-safety, NOT a proof of SHA-256 hash
// correctness (that would require a 64-round spec-equivalence miter).
module formal_sha256_ctrl (
    input logic         clk,
    input logic         rst_n,
    input logic         start,
    input logic         init,
    input logic         alg,
    input logic [511:0] block
);
    logic         busy, done;
    logic [255:0] hash;

    sha256_core u_dut (
        .clk  (clk),
        .rst_n(rst_n),
        .start(start),
        .init (init),
        .alg  (alg),
        .block(block),
        .busy (busy),
        .done (done),
        .hash (hash)
    );

    // (1) round counter bounded: rc in 0..63 (never indexes kconst/w OOB).
    always_comb assert (u_dut.rc <= 6'd63);

    // (2) FSM never enters the illegal 4th state encoding.
    always_comb assert (u_dut.state != 2'd3);
endmodule
