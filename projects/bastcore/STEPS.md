# BastCore — Build STEPS

> Deity: Bastet (protection) · Domain: BF16 tensor core · Spec: [docs/05_BastCore_BF16Tensor.md](../../docs/05_BastCore_BF16Tensor.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: bf16 matmul (bf16 inputs, fp32 accumulate) + 16x16 systolic dataflow pymodel. Phase 2 IN PROGRESS: bast_mac.sv — the MAC processing element (bf16 multiply -> exact bf16->fp32 widen -> registered fp32 accumulate) composing the verified HapiCore hapi_bf16_mul + hapi_fp32_add; cocotb-verified bit-exact vs golden.matmul on 400 variable-length dot products. Phase 3: generic Yosys synth 0 latches (~2729 cells incl. submodules, 32 acc flip-flops). 16x16 mac_grid + ASAP7 pending.

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | 🔧 |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | 🔧 |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ⬜ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | ⬜ |

**Depends on:** [hapicore](../hapicore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/bastcore/tests -v
# 2. read its checkpoints + tests
cat projects/bastcore/CHECKPOINTS.md projects/bastcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
