# BastCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| B2.1 | P0 | Golden: bf16 matmul (fp32 accumulate) | ✅ |
| B2.2 | P1 | pymodel: systolic MAC array | ✅ |
| B2.5 | P2 | RTL: mac_cell (bf16 mul + fp32 accumulate) + cocotb vs golden | ✅ |
| B2.6 | P2 | RTL: mac_grid RxC systolic array (abuttable to 16x16) + cocotb | ✅ |
| B2.8 | P3 | Synthesis: generic Yosys, 0 latches + gate count | ✅ |
| B2.9 | P4 | P&R: full array GDSII | ✅ |
| B2.10 | P5 | Signoff: formal proof of int8 MAC commutativity (k-induction, yosys-smtbmc+z3) | 🔧 |

**Progress:** 6/7 checkpoints complete (33% of phases).
