# GebCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| G.1 | P0 | Golden: 2:4 compress + sparse matmul | ✅ |
| G.2 | P1 | pymodel: metadata-driven MAC | ✅ |
| G.3 | P2 | RTL: sparse-MAC cell (lane-select + fp32 MAC) + cocotb vs golden | ✅ |
| G.4 | P3 | Synthesis: generic Yosys, 0 latches + gate count | ✅ |
| G.5 | P2 | RTL: sparse PE array (abuttable) | ⬜ |
| G.6 | P4 | P&R: GDSII | 🔧 |
| G.7 | P5 | Signoff: formal proof of geb_prune 2:4 invariant (exactly 2 kept, yosys-smtbmc+z3) | ✅ |

**Progress:** 5/7 checkpoints complete (33% of phases).
