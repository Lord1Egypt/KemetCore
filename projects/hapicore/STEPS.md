# HapiCore — Build STEPS

> Deity: Hapi (Nile flood) · Domain: IEEE-754 FPU library · Spec: [docs/09_HapiCore_FPU.md](../../docs/09_HapiCore_FPU.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: fp16/bf16/fp32 add, mul, fma, cmp, classify with correct bf16 round-to-nearest-even. Phase 2 IN PROGRESS: bf16 AND fp32 multiplier + adder RTL (hapi_bf16_mul/add, hapi_fp32_mul/add), each cocotb-verified bit-exact vs the golden/numpy (subnormals in+out, RNE, Inf/NaN/signed-zero, cancellation). Phase 3: generic Yosys synth 0 latches (bf16 mul ~873/add ~650; fp32 mul ~5046/add ~1792 cells). PLUS hapi_fp16_mul (IEEE half, 1/5/10): the bf16 multiplier widened to 11-bit significands / 22-bit product / biased exp = expa+expb-14-lz, cocotb bit-exact vs golden.fp_mul(.,.,'fp16') (numpy float16) on corners + 8K random + subnormal/overflow edges, Yosys 0-latch ~1390 cells. AND hapi_fp16_add (bf16 adder widened: 20-bit align frame, 11-bit keep, overflow exp>=31), cocotb bit-exact vs golden.fp_add fp16 on corners + 8K random + 3K cancellation + edges, Yosys 0-latch ~733 cells. fp32 add unblocks the BastCore tensor-core accumulate. PLUS hapi_fp32_fma (fused multiply-add, the headline ML MAC): exact 48-bit product + 24-bit addend aligned into a 128-bit window (full product width + cancellation headroom + guard) with sticky tail + sticky-borrow on effective subtract, one RNE; the GOLDEN fp_fma was upgraded to a genuine single rounding (exact rational a*b+c via fractions.Fraction, fulfilling its docstring — the old fp64 intermediate double-rounded). cocotb bit-exact on 190K+ FMAs (corners+random+cancellation+opposite-sign far-tail+subnormal/overflow); Yosys 0-latch via coarse synth (~686 word-level cells; ABC gate-mapping the wide alignment cloud is very slow, so it is deferred to Phase-4 PDK mapping — locally abc -fast gives ~43.5K AND/NOT gates). The FMA datapath was then GENERALISED into a parameterized hapi_fma_core (EXP_W/MANT_W/BIAS/W) with thin wrappers hapi_bf16_fma (W=48) + hapi_fp16_fma (W=48): each cocotb bit-exact vs the single-rounded golden on 150K+ FMAs, Yosys 0-latch full ABC (bf16 ~2961 / fp16 ~3411 gates locally). cocotb for all FMAs runs in CI, but FMA SYNTH is skipped under CI (apt-yosys OOMs on the priority-encoder/shifter cloud even for the small cores; committed .stat = evidence). FMA complete across bf16/fp16/fp32. PLUS hapi_fp32_div (correctly-rounded fp32 divide): normalise both significands to [2^23,2^24), one exact integer divide of a 51-bit dividend (Sa<<27) by the 24-bit divisor — quotient gives 24 sig bits + guard, the DIVISION REMAINDER is the exact sticky — then the FMA-style magnitude round (RNE, subnormal, overflow). Golden fp_div = _round_frac of exact Fraction(a)/Fraction(b). cocotb bit-exact on 165K+ divisions; Yosys 0-latch (coarse ~265 cells; abc-fast ~41.4K gates via $div, so div synth is also CI-skipped). PLUS hapi_fp32_sqrt (correctly-rounded sqrt): every fp32 sqrt is NORMAL (no subnormal/overflow), so normalise x=M*2^G, set radicand F=M or 2M for even exponent, one exact unrolled integer sqrt of F<<28 -> 24 sig bits + guard, the sqrt REMAINDER = sticky, then the same magnitude round. Golden fp_sqrt rounds the exact real sqrt via math.isqrt with exact tie detection. cocotb bit-exact on 210K+ roots (incl 4K perfect squares); 0-latch (coarse ~381 cells; abc-fast ~27K gates, sqrt synth also CI-skipped). HapiCore FPU now has mul+add+fma(x3 fmts)+div+sqrt. Phase 4: hapi_fp32_mul, hapi_fp16_mul, hapi_bf16_mul, hapi_bf16_add, hapi_fp32_add, and hapi_fp32_to_int signed off on ASAP7 7nm (registered boundary, WNS 0.00).

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

**Depends on:** none

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/hapicore/tests -v
# 2. read its checkpoints + tests
cat projects/hapicore/CHECKPOINTS.md projects/hapicore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
