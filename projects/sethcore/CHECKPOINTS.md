# SethCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| S2.1 | P0 | Golden: RV32I ISA simulator | 🔧 |
| S2.2 | P0 | Golden: M-extension (mul/div/rem) | 🔧 |
| S2.3 | P1 | pymodel: 5-stage pipeline | 🔧 |
| S2.4 | P1 | pymodel: hazard forwarding | 🔧 |
| S2.7 | P2 | RTL: ALU (seth_alu) + cocotb vs golden | 🔧 |
| S2.8 | P2 | RTL: mul/div (seth_muldiv) + cocotb vs golden | 🔧 |
| S2.8b | P2 | RTL: iterative mul/div (seth_muldiv_seq, P&R-friendly) + cocotb | 🔧 |
| S2.12 | P2 | RTL: immediate generator (seth_imm) + cocotb vs golden | 🔧 |
| S2.13 | P2 | RTL: register file (seth_regfile) + cocotb vs reference | 🔧 |
| S2.15 | P2 | RTL: ALU-control decoder (seth_aluctl) + exhaustive cocotb | 🔧 |
| S2.16 | P2 | RTL: main control decoder (seth_decode) + cocotb vs golden | 🔧 |
| S2.17 | P2 | RTL: integrated single-cycle core (seth_core) + cocotb vs ISA sim | 🔧 |
| S2.18 | P2 | RTL: 5-stage interlocked pipeline (seth_pipeline) + cocotb vs ISA sim | 🔧 |
| S2.10 | P2 | RTL: forwarding pipeline (seth_pipeline_fwd) + cocotb vs interlock & ISA sim | 🔧 |
| S2.19 | P2 | RTL: multi-cycle RV32IMZicsr core (seth_core_seq, iterative div, stall) vs CpuZ | 🔧 |
| S2.9 | P3 | Synthesis: ALU Yosys, 0 latches | 🔧 |
| S2.11 | P2 | cocotb: per-instruction vs Spike | ⬜ |
| S2.14 | P4 | P&R: core macro | 🔧 |
| S2.20 | P5 | Signoff: formal proof of seth_alu algebraic identities (yosys-smtbmc+z3, exhaustive) | 🔧 |
| S2.21 | P5 | Signoff: formal equivalence seth_muldiv_seq==seth_muldiv on short-latency paths (multiplies + special-case divides) — BMC from reset, anyconst operands, mutation-tested | 🔧 |
| S2.22 | P5 | Signoff: formal control-safety of seth_muldiv_seq handshake (done⊕busy mutual exclusion + single-cycle done pulse) — BMC over all input sequences to depth 40, mutation-tested | 🔧 |
| S2.23 | P5 | Signoff: formal bounded-termination of seth_muldiv_seq (iterative divide always finishes; busy never continuously high >33 cycles, bound proven tight) — mutation-tested | 🔧 |

**Progress:** 21/22 checkpoints complete (100% of phases).
