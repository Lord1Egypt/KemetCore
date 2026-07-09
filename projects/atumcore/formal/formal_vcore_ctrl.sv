// AtumCore — FORMAL: atum_vcore CONTROL-SAFETY invariants.
//
// The actual assertions live inside projects/atumcore/rtl/atum_vcore.sv under
// `ifdef FORMAL (compiled only when -DFORMAL is passed, so cocotb/Verilator and
// synthesis never see them). They must be embedded in the DUT because yosys 0.65
// resolves NEITHER cross-module hierarchical references (a wrapper's `u.vl` is
// silently treated as an implicitly-declared free wire -> vacuous proof) NOR the
// SystemVerilog `bind` construct (the checker module is dropped as "unused").
//
// The two properties, proved by temporal k-induction over the real RTL for EVERY
// reachable state and any program / imem-dmem-vreg preload sequence:
//
//   (1) VL-IN-RANGE — the architectural vector length never exceeds VLMAX.  This
//       is the core RVV safety invariant: every VLD/VST gather-scatter loop and
//       every masked lane write gates on `i < vl`, so vl > VLMAX would drive
//       out-of-range element and memory indices.  NON-tautological: vl is a
//       $clog2(VLMAX+1)-bit register (4 bits at VLMAX=8) that CAN hold 9..15 —
//       the proof shows atum_vsetvl's min(avl,VLMAX) saturation keeps it <= 8.
//                                                     [ vl <= VLMAX ]
//   (2) HALT-IS-STICKY — once the core halts (VHALT) it never spuriously
//       un-halts until reset, so `halted`/`dbg_pc` are a stable terminus the
//       golden-compare harness can rely on.        [ $past(halted) |-> halted ]
//
// TRACTABILITY: the heavy vector datapath (atum_vexec, atum_vregfile — and the
// whole tree of dividers / sqrt / fp units under vexec) is BLACKBOXED for the
// proof. vl, halted and pc do not depend on their outputs, so blackboxing is
// sound and keeps the SMT problem tiny (proved in <0.1 s) instead of dragging
// in divider/sqrt logic that does not converge under z3.
//
// This is CONTROL-SAFETY, strictly stronger than the random cocotb strip-mined
// programs (which only exercise the concrete vl/halt sequences they run) but NOT
// a proof of vector ALU numeric correctness — that stays covered bit-exact by
// tb/test_vcore.py against the golden VectorUnit.
//
// MUTATION-TESTED (proof is genuine, not vacuous): setting vl from the raw imm8
// instead of the saturated vsetvl output makes (1) FAIL; clearing `halted` on a
// preload makes (2) FAIL; the un-mutated RTL PASSES.
//
// This file is intentionally a documentation stub — run_formal.sh reads
// atum_vcore.sv directly with -DFORMAL (and blackboxes the datapath).
package atum_vcore_formal_note_pkg;
endpackage
