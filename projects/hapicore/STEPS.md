# HapiCore — Build STEPS

> Deity: Hapi (Nile flood) · Domain: IEEE-754 FPU library · Spec: [docs/09_HapiCore_FPU.md](../../docs/09_HapiCore_FPU.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: fp16/bf16/fp32 add, mul, fma, cmp, classify with correct bf16 round-to-nearest-even. Phase 2 IN PROGRESS: bf16 AND fp32 multiplier + adder RTL (hapi_bf16_mul/add, hapi_fp32_mul/add), each cocotb-verified bit-exact vs the golden/numpy (subnormals in+out, RNE, Inf/NaN/signed-zero, cancellation). Phase 3: generic Yosys synth 0 latches (bf16 mul ~873/add ~650; fp32 mul ~5046/add ~1792 cells). PLUS hapi_fp16_mul (IEEE half, 1/5/10): the bf16 multiplier widened to 11-bit significands / 22-bit product / biased exp = expa+expb-14-lz, cocotb bit-exact vs golden.fp_mul(.,.,'fp16') (numpy float16) on corners + 8K random + subnormal/overflow edges, Yosys 0-latch ~1390 cells. fp32 add unblocks the BastCore tensor-core accumulate. fp16 add, div/sqrt (Goldschmidt), fma, ASAP7 + P&R (Phase 4) pending.

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

**Depends on:** none

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/hapicore/tests -v
# 2. read its checkpoints + tests
cat projects/hapicore/CHECKPOINTS.md projects/hapicore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
