# HapiCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| HA.1 | P0 | Golden: fp16/bf16/fp32 add | ✅ |
| HA.2 | P0 | Golden: mul + fma | ✅ |
| HA.3 | P0 | Golden: IEEE specials (NaN/Inf/zero/subnormal) | ✅ |
| HA.4 | P0 | Golden: bf16 round-to-nearest-even | ✅ |
| HA.5 | P1 | pymodel: pipelined add/mul/fma (latency model) | ✅ |
| HA.8 | P2 | RTL: bf16 adder (hapi_bf16_add) + cocotb vs golden | ✅ |
| HA.9 | P2 | RTL: bf16 multiplier (hapi_bf16_mul) + cocotb vs golden | ✅ |
| HA.10 | P2 | RTL: fp32 adder (hapi_fp32_add) + cocotb vs golden/numpy | ✅ |
| HA.11 | P2 | RTL: fp32 multiplier (hapi_fp32_mul) + cocotb vs golden/numpy | ✅ |
| HA.12a | P2 | RTL: fp16 multiplier (hapi_fp16_mul) + cocotb vs golden/numpy | ✅ |
| HA.12b | P2 | RTL: fp16 adder (hapi_fp16_add) + cocotb vs golden/numpy | ✅ |
| HA.12 | P2 | RTL: fp_div (Goldschmidt) + fma | ⬜ |
| HA.13 | P3 | Synthesis: generic Yosys, 0 latches + gate count | ✅ |
| HA.14 | P3 | Synthesis: ASAP7 liberty tech-mapping | ⬜ |
| HA.15 | P4 | P&R: bf16/fp32 add+mul GDSII | ⬜ |

**Progress:** 12/15 checkpoints complete (33% of phases).
