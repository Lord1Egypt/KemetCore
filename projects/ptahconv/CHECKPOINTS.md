# PtahConv — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| PC.1 | P0 | Golden: conv2d (stride/pad) vs reference | ✅ |
| PC.2 | P1 | pymodel: tiled im2col dataflow | ✅ |
| PC.3 | P2 | RTL: systolic conv array | ⬜ |
| PC.4 | P4 | P&R: GDSII (tile-abutted) | 🔧 |
| PC.5 | P5 | Signoff: formal proof of ptah_bias_relu non-negativity (yosys-smtbmc+z3, all lanes) | 🔧 |

**Progress:** 2/5 checkpoints complete (33% of phases).
