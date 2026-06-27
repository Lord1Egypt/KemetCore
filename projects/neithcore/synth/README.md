# NeithCore Synthesis (Phase 3)

Generic Yosys synthesis of the NeithCore NTT primitives. Proves the cores are
synthesizable and **latch-free** (a Phase 3 exit gate) and gives a representative
gate count. ASAP7 liberty tech-mapping + OpenROAD P&R (Phase 4) is the next step.

## Run
```bash
# uses ~/miniconda3/envs/eda/bin/yosys by default; override with YOSYS=...
./run_synth.sh
```
The script asserts there are **no latches** (`$_DLATCH_*`/`$dlatch`) — it fails
loudly if synthesis infers any. Cell-count reports land in `reports/<core>.stat`.

## Results (generic synth, `synth` flow)
| Core | Cells (incl. submodules) | Latches | Notes |
|------|------:|:-------:|-------|
| `neith_modmul`   | ~1,427 | **0** | two integer multipliers + Barrett reduce |
| `neith_butterfly`| ~1,650 | **0** | modmul submodule + mod add/sub |

Counts are generic gates (not ASAP7-mapped); the modmul's two array multipliers
dominate. Both blocks are combinational (0 flip-flops). A multicycle 256-point NTT
engine that schedules one butterfly/cycle over a twiddle ROM + ping-pong RAM is the
natural Phase 2 follow-on. See `reports/*.stat` for the full breakdown.
