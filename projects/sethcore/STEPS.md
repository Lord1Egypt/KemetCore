# SethCore — Build STEPS

> Deity: Seth (strength) · Domain: RV32IM pipelined CPU · Spec: [docs/01_SethCore_RV32IM_CPU.md](../../docs/01_SethCore_RV32IM_CPU.md)

_Auto-generated from `tools/manifest.py` — do not edit by hand; edit the manifest and run `python tools/gen_tracking.py`._

**Scope (current):** Phase 0/1: RV32I+M ISA sim + 5-stage pymodel. Phase 2 IN PROGRESS: seth_alu.sv (RV32 ALU), seth_muldiv.sv (RV32M mul/div/rem) and seth_imm.sv (RV32 immediate generator: I/S/B/U/J formats, sign-extended per ISA) and seth_regfile.sv (32x32 register file: 2 async read ports + 1 sync write port, x0 hardwired 0) and seth_aluctl.sv (ALU-control decoder: opcode/funct3/funct7 -> 4-bit ALU select) all cocotb-verified vs golden/reference (decode_imm + decode_aluop added to the golden; aluctl swept EXHAUSTIVELY over all 2^17 inputs); fetch/decode + pipeline datapath RTL pending. Phase 3: ALU + imm + regfile + aluctl Yosys-synthesized 0 latches (imm ~92, regfile ~3.8K/992 DFFs, aluctl ~38 cells); combinational divider synth deferred (needs a sequential/iterative divider — generic synth explodes).

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
