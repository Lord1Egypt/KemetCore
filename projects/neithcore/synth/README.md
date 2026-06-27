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
| Core | Cells (incl. submodules) | Flip-flops | Latches | Notes |
|------|------:|:----------:|:-------:|-------|
| `neith_modmul`   | ~1,427 | 0 | **0** | two integer multipliers + Barrett reduce |
| `neith_butterfly`| ~1,650 | 0 | **0** | modmul submodule + mod add/sub |
| `neith_ntt`      | ~54,662 | ~3,373 | **0** | fwd+inv: 256×13 in-place memory + FSM + butterfly + 2 twiddle/scale modmuls |

Counts are generic gates (not ASAP7-mapped). The `neith_ntt` flip-flops are the
256×13-bit coefficient memory (3,328) plus a little control; Yosys lowers that array
to registers (no SRAM macro yet — an ASAP7 SRAM macro is the Phase 3/4 follow-on).
See `reports/*.stat` for the full breakdown.
