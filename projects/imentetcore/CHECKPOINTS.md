# ImentetCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| I.1 | P0 | Golden: scaled dot-product attention | ✅ |
| I.2 | P0 | Golden: stable softmax | ✅ |
| I.3 | P1 | pymodel: flash-tiled attention | ✅ |
| I.4 | P2 | RTL: softmax (LUT exp + Newton) | ✅ |
| I.5 | P4 | P&R: GDSII | ✅ |
| I.6 | P5 | Signoff: formal proof of attention-mask semantics — visible(m=0)=>score kept, masked(m=-inf)=>-inf (yosys-smtbmc+z3, all scores) | 🔧 |

**Progress:** 5/6 checkpoints complete (33% of phases).
