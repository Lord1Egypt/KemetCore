# HapiCore Synthesis (Phase 3)

Generic Yosys synthesis of the HapiCore FPU datapath (bf16 + fp32). Proves the cores
are synthesizable and **latch-free** (a Phase 3 exit gate) and gives a representative
gate count. ASAP7 liberty tech-mapping + OpenROAD P&R (Phase 4) is the next step.

## Run
```bash
# uses ~/miniconda3/envs/eda/bin/yosys by default; override with YOSYS=...
./run_synth.sh
```
The script asserts there are **no latches** (`$_DLATCH_*`/`$dlatch`) — it fails
loudly if synthesis infers any. Cell-count reports land in `reports/<core>.stat`.

## Results (generic synth, `synth` flow)
| Core | Cells | Flip-flops | Latches | Notes |
|------|------:|-----------:|:-------:|-------|
| `hapi_bf16_mul` | ~873 | 0 | **0** | bf16 multiplier (8×8 product) |
| `hapi_bf16_add` | ~650 | 0 | **0** | bf16 adder |
| `hapi_fp32_mul` | ~5,046 | 0 | **0** | fp32 multiplier (24×24 product) |
| `hapi_fp32_add` | ~1,792 | 0 | **0** | fp32 adder (49-bit align field) |

Counts are generic gates (not ASAP7-mapped). All blocks are combinational
(0 flip-flops); a pipelined wrapper with the 2-cycle latency from the pymodel
(`LATENCY["mul"]=2`) is a Phase 4 packaging step. See `reports/*.stat` for the
full breakdown and `reports/*.log` for the Yosys log.
