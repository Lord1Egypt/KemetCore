// AnubisCore — FORMAL: SHA-256 core CONTROL-SAFETY invariants.
//
// The actual assertions live inside projects/anubiscore/rtl/sha256_core.sv under
// `ifdef FORMAL (compiled only when -DFORMAL is passed, so cocotb/Verilator and
// synthesis never see them). They must be embedded in the DUT because yosys 0.65
// resolves NEITHER cross-module hierarchical references (a wrapper's `u.rc` is
// silently treated as an implicitly-declared free wire -> vacuous proof) NOR the
// SystemVerilog `bind` construct (the checker module is dropped as "unused").
//
// The two properties, proved by temporal k-induction over the real RTL for EVERY
// reachable state and any sequence of start/init/alg/block inputs:
//
//   (1) EXACTLY-64-ROUNDS — the FSM reaches FIN only when the round counter has
//       run the full 0..63 schedule (no block absorbed with the wrong round
//       count).  [ state == FIN |-> rc == 63 ]
//   (2) NO-ILLEGAL-STATE — the 2-bit state register never enters the unused 4th
//       encoding.  [ state != 2'd3 ]
//
// SHA-256/SHA-3 are designed to have no exploitable algebraic structure, so there
// is no cheap functional property to prove; this is CONTROL-SAFETY, not a proof
// of hash correctness (that would need a 64-round spec-equivalence miter). It is
// still strictly stronger than the random cocotb block-hash vectors, which only
// exercise the counter/state along the concrete round sequences they run.
//
// This file is intentionally a documentation stub — run_formal.sh reads
// sha256_core.sv directly with -DFORMAL.
package anubis_formal_note_pkg;
endpackage
