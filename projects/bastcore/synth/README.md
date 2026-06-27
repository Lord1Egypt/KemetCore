# BastCore Synthesis (Phase 3)

Generic Yosys synthesis of the BastCore MAC cell. Proves it is synthesizable and
**latch-free** (a Phase 3 exit gate) and gives a representative gate count. The MAC
pulls in the HapiCore primitives it instantiates. ASAP7 tech-mapping + OpenROAD P&R
(Phase 4), and the full 16×16 array, are the next steps.

## Run
```bash
# uses ~/miniconda3/envs/eda/bin/yosys by default; override with YOSYS=...
./run_synth.sh
```
The script asserts there are **no latches** (`$_DLATCH_*`/`$dlatch`) — it fails
loudly if synthesis infers any. The report lands in `reports/bast_mac.stat`.

## Results (generic synth, `synth` flow)
| Core | Cells (incl. submodules) | Flip-flops | Latches | Notes |
|------|------:|:----------:|:-------:|-------|
| `bast_mac` | ~2,729 | 32 | **0** | hapi_bf16_mul + hapi_fp32_add + 32-bit fp32 acc register |

The 32 flip-flops are the fp32 accumulator; the combinational bulk is the fp32 adder
(~1,792) and bf16 multiplier (~873). A 16×16 grid abuts 256 of these PEs — the
tile-abutment strategy from PtahCore applies. See `reports/bast_mac.stat` for the
full breakdown.
