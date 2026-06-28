# SethCore — Build STEPS

> Deity: Seth (strength) · Domain: RV32IM pipelined CPU · Spec: [docs/01_SethCore_RV32IM_CPU.md](../../docs/01_SethCore_RV32IM_CPU.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: RV32I+M ISA sim + 5-stage pymodel. Phase 2 IN PROGRESS: seth_alu.sv (RV32 ALU), seth_muldiv.sv (RV32M mul/div/rem) and seth_imm.sv (RV32 immediate generator: I/S/B/U/J formats, sign-extended per ISA) and seth_regfile.sv (32x32 register file: 2 async read ports + 1 sync write port, x0 hardwired 0) and seth_aluctl.sv (ALU-control decoder: opcode/funct3/funct7 -> 4-bit ALU select) all cocotb-verified vs golden/reference (decode_imm + decode_aluop added to the golden; aluctl swept EXHAUSTIVELY over all 2^17 inputs) and seth_decode.sv (main control decoder: opcode/funct7 -> 10-signal datapath control word reg_write/alu_src_imm/a_src_pc/mem_read/mem_write/branch/jump/jalr/is_mdu/wb_sel, vs golden.decode_ctrl). INTEGRATED into seth_core.sv — a working single-cycle RV32IM core (fetch + word memory + all blocks wired + branch/jump control flow + load/store byte/half/word); the register file gained a synchronous reset for deterministic boot. seth_core runs the golden's programs (sum, fibonacci, mul/div + load/store + lui/auipc) and 40 randomised ALU/M programs with the FULL final register file matching the ISA sim. PIPELINED into seth_pipeline.sv — a 5-stage IF/ID/EX/MEM/WB core with full INTERLOCK STALLS (no forwarding yet; ID stalls until a needed source reg's producer leaves the EX/MEM/WB window) + branch/jump flush in EX (2-cycle penalty); the same programs plus a dependent-chain + branch-flush stress + 120 random programs all match the ISA sim. Remaining: add FORWARDING (performance only; results identical). Phase 3: ALU + imm + regfile + aluctl + decode full-synth 0 latches (imm ~92, regfile ~3.8K/992 DFFs, aluctl/decode ~38 cells); seth_core + seth_pipeline coarse 0-latch (memory -> $mem, CPU synth CI-skipped); combinational divider full synth deferred (generic synth explodes).

## Ordered steps (6-phase lifecycle)

| # | Phase | Step | Status |
|:-:|:-----:|------|:------:|
| 1 | P0 | Write the numpy/pure-python golden reference (the mathematical truth) | ✅ |
| 2 | P0 | Write golden tests vs known-correct software; achieve passing pytest | ✅ |
| 3 | P1 | Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit | ✅ |
| 4 | P2 | Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90% | 🔧 |
| 5 | P3 | Yosys synthesis: 0 latches, gate count <= target | 🔧 |
| 6 | P4 | OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII | ⬜ |
| 7 | P5 | CI pipeline + docs finalization; `make all` green | ⬜ |

**Depends on:** [hapicore](../hapicore/STEPS.md)

## How to resume this project

```bash
# 1. run its tests (Phase 0/1 must stay green)
pytest projects/sethcore/tests -v
# 2. read its checkpoints + tests
cat projects/sethcore/CHECKPOINTS.md projects/sethcore/TESTS.md
# 3. continue from the first ⬜ step above (next phase = RTL)
```
