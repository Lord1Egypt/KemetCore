# AtumCore — Build STEPS

> Deity: Atum (creator) · Domain: RISC-V Vector (RVV) unit · Spec: [docs/10_AtumCore_RVV.md](../../docs/10_AtumCore_RVV.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1 implements an RVV-subset golden (vsetvl, vadd/vsub/vmul/vmacc, logic/shift, masked ops, vfadd/vfmul, vredsum) and an 8-lane pymodel. Phase 2 IN PROGRESS: atum_valu.sv — a VLMAX(=8)-lane combinational vector integer ALU (add/sub/mul/and/or/xor/sll/srl + vmacc vd+=vs1*vs2) with full RVV active-element semantics: a lane writes only when body-active (i<vl) AND mask-active, else the destination element is undisturbed; operands packed little-endian by lane. Bit-exact vs the golden VectorUnit on directed corners + 6000 random ops (all ops/VL/mask). Phase 3: atum_valu full-synth 0 latches (~33K cells, eight 32-bit multipliers; CI uses a coarse 0-latch check, committed .stat is the full gate-level evidence). atum_vfpu.sv — the fp32 vector lane (vfadd/vfmul) composing the bit-exact HapiCore fp32 cores (hapi_fp32_add/mul) per lane with the same active-element write; bit-exact vs golden on fp corners (zeros/inf/nan/subnormal/overflow) + 5000 random; 0-latch (CI coarse). atum_vredu.sv — the vector reduction unit (vredsum = 32-bit wrapping sum, vredmax) over active lanes (i<vl AND mask), scalar result; note the golden widens uint32->int64 so vredmax is an UNSIGNED max (identity 0) — matched bit-for-bit. Bit-exact vs golden on directed + 6000 random vredsum+vredmax; full-synth 0 latches (~3.1K cells). atum_vexec.sv — the integrated vector execute unit: decodes a vclass (0=ALU->atum_valu, 1=FP->atum_vfpu, 2=RED->atum_vredu) + subop and muxes to one uniform vector output (a reduction scalar lands in element 0, the rest keep vd_old). AtumCore's integration capstone (like seth_core for SethCore). Bit-exact vs golden on directed + 6000 random MIXED ops (int incl vmacc / fp vfadd-vfmul / vredsum-vredmax); 0-latch (CI coarse). atum_vregfile.sv — NREGS x VLEN vector register file (2 async read + 1 sync write, sync reset, no hardwired-zero since RVV v0 is a mask reg) verified on 4000 rw cycles; atum_vsetvl.sv — VL = min(AVL, VLMAX) combinational, vs golden on edges + 2000 random. Both full-synth 0 latches (vregfile ~40.8K cells DFF-heavy, vsetvl ~32). atum_vcore.sv — a SINGLE-CYCLE VECTOR CORE (AtumCore's seth_core equivalent): fetch a 32-bit micro-op (VSETVL/VOP/VHALT; vd/vs1/vs2/vclass/subop/avl fields) -> 3-port vregfile read -> atum_vexec -> writeback, one op/cycle, VL gates the body, mask all-ones. TB preloads imem + initial vregs, runs to HALT, compares the whole vector regfile to a golden runner executing the same micro-program on VectorUnit. Bit-exact on a directed program (int axpy/dot + fp vfmul/vfadd + vredsum/vredmax + partial-vl) + 40 random programs; 0-latch (CI coarse). The core gained a word-addressable VECTOR DATA MEMORY with unit-stride VLD/VST micro-ops (3-bit opcode; VLD overwrites vd from dmem[base+i] for i<vl else 0, VST writes vs1 lanes to dmem[base+i]); it now runs a real STRIP-MINED integer axpy (vsetvl + VLD/VMACC/VST over a length-20 array) and the TB checks the whole machine state (vregfile + data memory) vs the golden runner on the axpy + 40 random load/store/op/reduction programs. AtumCore is a complete working vector processor. Phase 4: atum_valu, atum_vredu, atum_vsadd, atum_vcompress, atum_viota, atum_vmask, atum_vsetvl, and atum_vfpu signed off on ASAP7 7nm (registered boundaries).

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | 🔧 |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | 🔧 |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | 🔧 |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | 🔧 |

**Depends on:** [sethcore](../sethcore/STEPS.md), [hapicore](../hapicore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/atumcore/tests -v
# 2. read its checkpoints + tests
cat projects/atumcore/CHECKPOINTS.md projects/atumcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
