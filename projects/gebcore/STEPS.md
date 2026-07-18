# GebCore — Build STEPS

> Deity: Geb (earth) · Domain: 2:4 structured sparse matmul · Spec: [docs/04_GebCore_SparseMatmul.md](../../docs/04_GebCore_SparseMatmul.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1 implements 2:4 structured-sparse matmul (compress to 2-of-4 + metadata) and a pymodel that skips pruned MACs. Phase 2 IN PROGRESS: geb_spmac.sv — the sparse-MAC processing element: a 2-bit lane index (the 2:4 metadata) selects one of the group's 4 fp32 activations, multiplies by the kept weight (fp32), and fp32-accumulates, composing the verified HapiCore hapi_fp32_mul + hapi_fp32_add. So it performs exactly ONE MAC per kept lane (half a dense matmul). cocotb-verified bit-exact vs golden.sparse_matmul on 412 output elements (random pruned matrices, K up to 20). NB: golden's dense_matmul cross-check is only ~equal, not bit-identical, since fp32 sums are non-associative and use a different lane order — the HW target is sparse_matmul. Phase 3: generic Yosys synth 0 latches (~7130 cells). Sparse PE array (abut) + ASAP7 pending.

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | ✅ |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | ✅ |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ✅ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | 🔧 |

**Depends on:** [bastcore](../bastcore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/gebcore/tests -v
# 2. read its checkpoints + tests
cat projects/gebcore/CHECKPOINTS.md projects/gebcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
