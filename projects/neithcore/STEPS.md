# NeithCore — Build STEPS

> Deity: Neith (war/wisdom) · Domain: ML-KEM (Kyber) lattice KEM · Spec: [docs/07_NeithCore_MLKEM.md](../../docs/07_NeithCore_MLKEM.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: negacyclic NTT over Z_q (q=7681, NTT-friendly) plus a Kyber-512-style module-LWE KEM that is self-consistent (decaps recovers the encaps shared secret). Phase 2 IN PROGRESS: neith_modmul (Barrett mult mod 7681) and neith_butterfly (Cooley-Tukey butterfly) RTL, both cocotb-verified bit-exact vs the golden. Phase 3: generic Yosys synth 0 latches (modmul ~1.4K, butterfly ~1.65K cells). Multicycle 256-pt NTT engine + FIPS-203 exact params (q=3329, incomplete NTT) + ASAP7 pending. NOTE: reference model, not FIPS-203 certified.

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
pytest projects/neithcore/tests -v
# 2. read its checkpoints + tests
cat projects/neithcore/CHECKPOINTS.md projects/neithcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
