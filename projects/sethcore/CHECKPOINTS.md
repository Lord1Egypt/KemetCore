# SethCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| S2.1 | P0 | Golden: RV32I ISA simulator | ✅ |
| S2.2 | P0 | Golden: M-extension (mul/div/rem) | ✅ |
| S2.3 | P1 | pymodel: 5-stage pipeline | ✅ |
| S2.4 | P1 | pymodel: hazard forwarding | ✅ |
| S2.7 | P2 | RTL: ALU (seth_alu) + cocotb vs golden | ✅ |
| S2.8 | P2 | RTL: mul/div (seth_muldiv) + cocotb vs golden | ✅ |
| S2.12 | P2 | RTL: immediate generator (seth_imm) + cocotb vs golden | ✅ |
| S2.13 | P2 | RTL: register file (seth_regfile) + cocotb vs reference | ✅ |
| S2.15 | P2 | RTL: ALU-control decoder (seth_aluctl) + exhaustive cocotb | ✅ |
| S2.16 | P2 | RTL: main control decoder (seth_decode) + cocotb vs golden | ✅ |
| S2.17 | P2 | RTL: integrated single-cycle core (seth_core) + cocotb vs ISA sim | ✅ |
| S2.18 | P2 | RTL: 5-stage interlocked pipeline (seth_pipeline) + cocotb vs ISA sim | ✅ |
| S2.10 | P2 | RTL: add forwarding to the pipeline (performance; result-invariant) | ⬜ |
| S2.9 | P3 | Synthesis: ALU Yosys, 0 latches | ✅ |
| S2.11 | P2 | cocotb: per-instruction vs Spike | ⬜ |
| S2.14 | P4 | P&R: core macro | ⬜ |

**Progress:** 13/16 checkpoints complete (33% of phases).
