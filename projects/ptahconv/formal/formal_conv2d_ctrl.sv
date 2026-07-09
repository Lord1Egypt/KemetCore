// PtahConv — FORMAL: ptah_conv2d CONTROL-SAFETY invariants.
//
// The actual assertions live inside projects/ptahconv/rtl/ptah_conv2d.sv under
// `ifdef FORMAL (compiled only when -DFORMAL is passed, so cocotb/Verilator and
// synthesis never see them). They must be embedded in the DUT because yosys 0.65
// resolves NEITHER cross-module hierarchical references (a wrapper's `u.state` is
// silently treated as an implicitly-declared free wire -> vacuous proof) NOR the
// SystemVerilog `bind` construct (the checker module is dropped as "unused").
//
// The two properties, proved by temporal k-induction over the real RTL for EVERY
// reachable state and any start/preload/config (H/W/K/stride/pad) sequence:
//
//   (1) NO-ILLEGAL-STATE — the 2-bit state register has 3 valid encodings
//       (IDLE/TAP/WB = 0/1/2); it never enters the unused 4th code 2'd3.  A
//       2-bit register CAN physically hold it, so this is NON-tautological: it
//       proves the control logic never drives one (the `default` arm is a
//       safety net, not a reachable transition).             [ state != 2'd3 ]
//   (2) DONE-ONLY-AT-REST — the completion pulse `done` is asserted ONLY in IDLE.
//       It never fires mid-convolution, so a consumer that reads the output
//       memory on `done` can never latch a partial result.  Couples the output
//       handshake to the FSM having actually returned to rest.
//                                                  [ done |-> state == IDLE ]
//
// This is CONTROL-SAFETY, strictly stronger than the random cocotb conv vectors
// (which only exercise the FSM along the concrete conv geometries they run) but
// NOT a proof of conv2d numeric correctness — the fp32 MAC datapath value
// correctness stays covered bit-exact by tb/test_conv2d.py against the golden.
//
// NOTE ON METHOD: ptah_conv2d uses SYNCHRONOUS reset, so there is no async-reset
// init value; the flops are unconstrained at t=0.  A plain BMC-from-reset would
// therefore see an arbitrary illegal initial state and spuriously fail.  Both
// properties are 1-INDUCTIVE, so they are proved by temporal k-induction
// (yosys-smtbmc -i): being inductive, they hold in every state closed under the
// transition relation, and in particular from the real reset state (IDLE,
// done=0) forward.
//
// MUTATION-TESTED (proof is genuine, not vacuous): making IDLE-on-start jump to
// state code 2'd3 makes (1) FAIL; raising `done` during TAP makes (2) FAIL; the
// un-mutated RTL PASSES.
//
// This file is intentionally a documentation stub — run_formal.sh reads
// ptah_conv2d.sv directly with -DFORMAL.
package ptah_conv2d_formal_note_pkg;
endpackage
