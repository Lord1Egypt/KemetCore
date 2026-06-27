# AnubisCore — Build STEPS

> Deity: Anubis (embalming) · Domain: SHA-256 / SHA-3 hash engine · Spec: [docs/06_AnubisCore_HashEngine.md](../../docs/06_AnubisCore_HashEngine.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: full SHA-256 + Keccak/SHA3-256 in pure Python vs hashlib. Phase 2 IN PROGRESS: synthesizable SHA-256 RTL (sha256_core.sv) verified bit-exact in cocotb/Verilator on 9 messages; Keccak RTL still pending. Phase 3+ (Yosys/OpenROAD) not started — no synth toolchain locally.

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | 🔧 |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | ⬜ |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ⬜ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | ⬜ |

**Depends on:** none

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/anubiscore/tests -v
# 2. read its checkpoints + tests
cat projects/anubiscore/CHECKPOINTS.md projects/anubiscore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
