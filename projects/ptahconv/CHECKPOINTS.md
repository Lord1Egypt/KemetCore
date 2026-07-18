# PtahConv — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| PC.1 | P0 | Golden: conv2d (stride/pad) vs reference | 🔧 |
| PC.2 | P1 | pymodel: tiled im2col dataflow | 🔧 |
| PC.3 | P2 | RTL: systolic conv array | 🔧 |
| PC.4 | P4 | P&R: GDSII (tile-abutted) | 🔧 |
| PC.5 | P5 | Signoff: formal proof of ptah_bias_relu non-negativity (yosys-smtbmc+z3, all lanes) | 🔧 |
| PC.6 | P5 | Signoff: formal control-safety of the conv2d FSM — no illegal state + done only at rest (temporal k-induction, mutation-tested) | 🔧 |

**Progress:** 6/6 checkpoints complete (100% of phases).
