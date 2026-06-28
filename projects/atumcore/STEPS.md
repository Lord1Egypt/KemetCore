# AtumCore — Build STEPS

> Deity: Atum (creator) · Domain: RISC-V Vector (RVV) unit · Spec: [docs/10_AtumCore_RVV.md](../../docs/10_AtumCore_RVV.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1 implements an RVV-subset golden (vsetvl, vadd/vsub/vmul/vmacc, logic/shift, masked ops, vfadd/vfmul, vredsum) and an 8-lane pymodel. Phase 2 IN PROGRESS: atum_valu.sv — a VLMAX(=8)-lane combinational vector integer ALU (add/sub/mul/and/or/xor/sll/srl) with full RVV active-element semantics: a lane writes only when body-active (i<vl) AND mask-active, else the destination element is undisturbed; operands packed little-endian by lane. Bit-exact vs the golden VectorUnit on directed corners + 6000 random ops (all ops/VL/mask). Phase 3: atum_valu full-synth 0 latches (~33K cells, eight 32-bit multipliers; CI uses a coarse 0-latch check, committed .stat is the full gate-level evidence). atum_vfpu.sv — the fp32 vector lane (vfadd/vfmul) composing the bit-exact HapiCore fp32 cores (hapi_fp32_add/mul) per lane with the same active-element write; bit-exact vs golden on fp corners (zeros/inf/nan/subnormal/overflow) + 5000 random; 0-latch (CI coarse).

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | ⬜ |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | ⬜ |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ⬜ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | ⬜ |

**Depends on:** [sethcore](../sethcore/STEPS.md), [hapicore](../hapicore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/atumcore/tests -v
# 2. read its checkpoints + tests
cat projects/atumcore/CHECKPOINTS.md projects/atumcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
