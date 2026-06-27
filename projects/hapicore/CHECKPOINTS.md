# HapiCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| HA.1 | P0 | Golden: fp16/bf16/fp32 add | ✅ |
| HA.2 | P0 | Golden: mul + fma | ✅ |
| HA.3 | P0 | Golden: IEEE specials (NaN/Inf/zero/subnormal) | ✅ |
| HA.4 | P0 | Golden: bf16 round-to-nearest-even | ✅ |
| HA.5 | P1 | pymodel: pipelined add/mul/fma (latency model) | ✅ |
| HA.8 | P2 | RTL: fp_add (parametric) | ⬜ |
| HA.9 | P2 | RTL: fp_mul (parametric) | ⬜ |
| HA.11 | P2 | RTL: fp_div (Goldschmidt) | ⬜ |
| HA.13 | P3 | Synthesis: gate count | ⬜ |
| HA.14 | P4 | P&R: fp32 add/mul/fma GDSII | ⬜ |

**Progress:** 5/10 checkpoints complete (33% of phases).
