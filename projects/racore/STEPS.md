# RaCore — Build STEPS

> Deity: Ra (supreme creator) · Domain: Heterogeneous AI SoC (capstone) · Spec: [docs/00_RaCore_SoC.md](../../docs/00_RaCore_SoC.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1 implements the KAI register/DMA contract model, a NoC + descriptor-DMA functional model, a KAI conformance harness, and an end-to-end axpy that drives a KAI accelerator through the fabric. Phase 4 DONE: ra_noc_arbiter and ra_kai_regs signed off on ASAP7 7nm (WNS 0.00, 0 route-DRC, flow/HARDEN_RESULTS.md), matching the representative-block bar used for the other cores. RA.10's earlier hierarchical Lite GDSII checkpoint is the same evidence. Full SoC-level GDSII (RaCore-Full, all 11 accelerators integrated) is a separate, much harder item, not attempted here.

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | 🔧 |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | 🔧 |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ✅ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | 🔧 |

**Depends on:** [sethcore](../sethcore/STEPS.md), [atumcore](../atumcore/STEPS.md), [hapicore](../hapicore/STEPS.md), [anubiscore](../anubiscore/STEPS.md), [bastcore](../bastcore/STEPS.md), [ptahconv](../ptahconv/STEPS.md), [gebcore](../gebcore/STEPS.md), [imentetcore](../imentetcore/STEPS.md), [neithcore](../neithcore/STEPS.md), [sobekcore](../sobekcore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/racore/tests -v
# 2. read its checkpoints + tests
cat projects/racore/CHECKPOINTS.md projects/racore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
