# PtahConv — Build STEPS

> Deity: Ptah (craftsmen) · Domain: Direct convolution accelerator · Spec: [docs/02_PtahConv_Convolution.md](../../docs/02_PtahConv_Convolution.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1 implements conv2d (NCHW, stride/pad) via im2col+matmul golden and a tiled dataflow pymodel.

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

**Depends on:** [bastcore](../bastcore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/ptahconv/tests -v
# 2. read its checkpoints + tests
cat projects/ptahconv/CHECKPOINTS.md projects/ptahconv/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
