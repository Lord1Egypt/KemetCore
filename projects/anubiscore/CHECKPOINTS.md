# AnubisCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| A1.1 | P0 | Golden: SHA-256 vs hashlib | ✅ |
| A1.2 | P0 | Golden: Keccak-f[1600] / SHA3-256 vs hashlib | ✅ |
| A1.3 | P0 | Golden: NIST-style vectors (empty/abc/long) | ✅ |
| A1.4 | P1 | pymodel: SHA-256 round engine (64 rounds) | ✅ |
| A1.5 | P1 | pymodel: Keccak round engine (24 rounds) | ✅ |
| A1.6 | P2 | RTL: SHA-256 datapath + cocotb (Verilator) | ✅ |
| A1.7 | P2 | RTL: Keccak-f[1600] | ⬜ |
| A1.8 | P3 | Synthesis: Yosys gate count, 0 latches | ⬜ |
| A1.10 | P4 | P&R: GDSII | ⬜ |

**Progress:** 6/9 checkpoints complete (33% of phases).
