# AnubisCore Synthesis (Phase 3)

Generic Yosys synthesis of the AnubisCore RTL. Proves the cores are synthesizable
and **latch-free** (a Phase 3 exit gate) and gives a representative gate count.
ASAP7 liberty tech-mapping + OpenROAD P&R (Phase 4) is the next step.

## Run
```bash
# uses ~/miniconda3/envs/eda/bin/yosys by default; override with YOSYS=...
./run_synth.sh
```
The script asserts there are **no latches** (`$_DLATCH_*`/`$dlatch`) — it fails loudly
if synthesis infers any. Cell-count reports land in `reports/<core>.stat`.

## Results (generic synth, `synth` flow)
| Core | Cells | Flip-flops | Latches | Notes |
|------|------:|-----------:|:-------:|-------|
| `sha256_core`   | ~6,354  | ~1,035 | **0** | 64-round, 16-word schedule window |
| `sha3_256_core` | ~15,783 | ~1,610 | **0** | 1600-bit state, 24-round permutation |

Counts are generic gates (not ASAP7-mapped); they track the architectural size
(SHA3's 1600-bit state dominates). See `reports/*.stat` for the full breakdown and
`reports/*.log` for the full Yosys log.
