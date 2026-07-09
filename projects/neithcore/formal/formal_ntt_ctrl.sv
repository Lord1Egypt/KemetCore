// NeithCore — FORMAL: neith_ntt (256-point NTT engine) CONTROL-SAFETY invariants.
//
// The actual assertions live inside projects/neithcore/rtl/neith_ntt.sv under
// `ifdef FORMAL (compiled only when -DFORMAL is passed, so cocotb/Verilator and
// synthesis never see them). They must be embedded in the DUT because yosys 0.65
// resolves NEITHER cross-module hierarchical references (a wrapper's `u.state` is
// silently treated as an implicitly-declared free wire -> vacuous proof) NOR the
// SystemVerilog `bind` construct (the checker module is dropped as "unused").
//
// The two properties, proved by temporal k-induction over the real RTL for EVERY
// reachable state and any sequence of start/mode/nega/in_valid/rd_addr inputs:
//
//   (1) NO-ILLEGAL-STATE — the 3-bit state register has 5 valid encodings
//       (S_IDLE..S_DONE = 0..4); it never enters an unused code 5/6/7.  A 3-bit
//       register CAN physically hold those codes, so this is NON-tautological: it
//       proves the control logic never drives one (the `default` arm is a safety
//       net, not a reachable transition).                 [ state <= S_DONE ]
//   (2) SCALE-IS-INVERSE — the inverse-only 1/N (+psi^-i) scaling pass runs ONLY
//       when the latched transform direction is inverse.  Couples the control FSM
//       to the mode latched at start: a FORWARD NTT can never enter the scaling
//       pass, which would corrupt its result by the spurious 256^-1 factor.
//                                             [ state == S_SCALE |-> mode_reg ]
//
// This is CONTROL-SAFETY, strictly stronger than the random cocotb NTT vectors,
// which only exercise the FSM along the concrete forward/inverse/negacyclic
// sequences they run.  It is NOT a proof of NTT numeric correctness (that would
// need a full 8-stage butterfly-network spec-equivalence miter — the mod-Q
// twiddle datapath is a divider-equivalence problem that does not converge under
// z3; the bit-exact cocotb testbench against golden.ntt/intt covers value
// correctness, this covers that the control sequencing is always well-formed).
//
// MUTATION-TESTED (proof is genuine, not vacuous): injecting a transition into
// state code 3'd5 makes (1) FAIL; entering S_SCALE regardless of mode_reg makes
// (2) FAIL; the un-mutated RTL PASSES.
//
// This file is intentionally a documentation stub — run_formal.sh reads
// neith_ntt.sv directly with -DFORMAL.
package neith_ntt_formal_note_pkg;
endpackage
