# 𓁹 SethCore — RISC-V RV32IM Pipelined CPU Core

> **Deity:** Seth (𓁹, god of chaos, strength, and the desert)
> **Domain:** CPU Architecture
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 500 MHz on ASAP7
> **Est. Gates:** ~50K
> **Complexity:** ★★★★☆

---

## 1. Technical Overview

SethCore is a 5-stage in-order pipelined RISC-V CPU core implementing the RV32I base instruction set plus the M extension (integer multiply/divide). It features a classic Harvard microarchitecture with separate instruction and data memory interfaces, full data forwarding to eliminate data hazards, and a branch predictor for control hazard mitigation.

### Key Innovations vs. Prior Art

| Feature | SethCore | Typical Teaching Core (picorv32, SERV) |
|---------|----------|----------------------------------------|
| Pipeline | 5-stage (F/D/E/M/W) | 2–3 stage or state machine |
| Multiply | Pipelined 32-bit (4-cycle) | Iterative (32+ cycles) |
| Divide | Non-restoring (34-cycle signed) | Not implemented |
| Forwarding | Full forwarding network | None (stall everything) |
| Branch Predictor | 2-bit saturating counter + BTB | Always not-taken |
| Verification | Bit-exact vs Spike | Manual inspection |

### RISC-V Extensions

| Extension | Status | Details |
|-----------|--------|---------|
| RV32I | ✅ Required | All 40 base instructions |
| M | 🎯 Target | mul, mulh, mulhu, mulhsu, div, divu, rem, remu |
| Zicsr | 🎯 Target | CSRRW, CSRRS, CSRRC (machine-level only) |
| Zifencei | 🎯 Target | FENCE.I for instruction stream sync |

---

## 2. Architecture

### Pipeline Stages

```
 ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
 │ FETCH   │───▶│ DECODE  │───▶│ EXECUTE │───▶│ MEMORY  │───▶│ WRITEBK │
 │         │    │         │    │         │    │         │    │         │
 │• PC+4   │    │• RF read│    │• ALU op │    │• D-cache│    │• RF wri │
 │• I-cache│    │• imm gen│    │• MUL op │    │• LSU   │    │• fwd    │
 │• BPred  │    │• hazard │    │• DIV op │    │        │    │         │
 └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
      │               │              │              │              │
      └───────────────┴───forwarding paths──────────┘──────────────┘
```

### Module Hierarchy

```
sethcore/
├── seth_core_top.sv          # Top-level: pipeline controller
├── seth_fetch.sv             # Fetch stage + PC logic
├── seth_fetch_buffer.sv      # F/D pipeline register
├── seth_decode.sv            # Decode + immediate generation
├── seth_decode_buffer.sv     # D/E pipeline register
├── seth_regfile.sv           # 32×32 register file (3R1W)
├── seth_execute.sv           # Execute stage + ALU
├── seth_execute_buffer.sv    # E/M pipeline register
├── seth_alu.sv               # Integer ALU (add/sub/slt/...)
├── seth_mul.sv               # Pipelined 32-bit multiplier
├── seth_div.sv               # Non-restoring divider
├── seth_memory.sv            # Memory stage + LSU
├── seth_memory_buffer.sv     # M/W pipeline register
├── seth_writeback.sv         # Writeback mux + forwarding
├── seth_hazard.sv            # Hazard detection unit
├── seth_forward.sv           # Forwarding unit
├── seth_bp.sv                # Branch predictor (2-bit + BTB)
├── seth_csr.sv               # Control & status registers
├── seth_icache.sv            # Instruction cache (2KiB)
├── seth_dcache.sv            # Data cache (2KiB)
└── seth_lsu.sv               # Load/store unit
```

### Memory Interface

| Interface | Width | Protocol | Description |
|-----------|-------|----------|-------------|
| I-cache | 64-bit | AXI4-lite | Instruction fetch |
| D-cache | 64-bit | AXI4-lite | Load/store data |
| Mem-AXI | 64-bit | AXI4-full | External memory |

---

## 3. Pipeline Hazard Handling

| Hazard Type | SethCore Strategy |
|-------------|--------------------|
| **RAW (read-after-write)** | Full forwarding from E, M, W stages; stall if load-use |
| **WAW (write-after-write)** | Impossible — single write port, in-order |
| **WAR (write-after-read)** | Impossible — in-order pipeline |
| **Control (branches)** | 2-bit predictor + BTB; 2-cycle mispredict penalty |
| **Structural (RF)** | 3-read 1-write register file; no structural stalls |

---

## 4. Golden Reference

### ISA Simulator (`golden/`)

```
golden/
├── isa.py                     # RV32IM instruction set simulator
├── registers.py               # Register file model
├── memory.py                  # Flat memory model
├── csr.py                     # CSR file model
├── decoder.py                 # Instruction decoder
├── executor.py                # Instruction executor
├── simulator.py               # Full-system simulator
└── tests/
    ├── test_isa.py            # Each instruction against known results
    ├── test_decoder.py        # 40 opcode decoding tests
    ├── test_mul.py            # Multiply exhaustive + random
    ├── test_div.py            # Divide exhaustive + random
    └── test_programs.py       # Small programs (fibonacci, quicksort)
```

### Spike Compatibility

The golden simulator must match **Spike** (the official RISC-V reference simulator) on every instruction. The test harness:

1. Generates a random RISC-V binary
2. Runs it through the golden simulator → captures register state
3. Runs it through Spike → captures register state
4. Asserts bit-exact match

---

## 5. pymodel (`pymodel/`)

```
pymodel/
├── pipeline.py                # 5-stage pipeline model
├── hazard.py                  # Hazard & forwarding logic
├── bp.py                      # Branch predictor model
├── cache.py                   # Cache model (LRU, set-associative)
├── sim.py                     # Top-level simulation harness
└── tests/
    ├── test_pipeline.py       # Pipeline correctness
    ├── test_hazard.py         # Hazard sequence stress
    ├── test_forwarding.py     # RAW coverage across all combinations
    ├── test_bp.py             # Branch prediction accuracy
    └── test_e2e.py            # Full program execution
```

---

## 6. RTL Modules & cocotb Tests

### Test Structure

```
rtl/
└── tb/
    ├── test_alu.py            # All ALU ops: directed + random (2,000 cases)
    ├── test_mul.py            # Cross-product + edge cases (1,000 cases)
    ├── test_div.py            # Non-restoring: quotient + remainder (500 cases)
    ├── test_regfile.py        # 3R1W: simultaneous reads, bypass
    ├── test_fetch.py          # PC alignment, branch target, BP flush
    ├── test_decode.py         # All 40+ instruction decodings
    ├── test_execute.py        # ALU + MUL + DIV in execute pipeline
    ├── test_memory.py         # LB/LH/LW/LBU/LHU + SB/SH/SW
    ├── test_hazard.py         # RAW + control hazard sequences
    ├── test_forwarding.py     # Forwarding path verification
    ├── test_bp.py             # Predictor state machine
    ├── test_csr.py            # CSR access patterns
    ├── test_cache.py          # Hit/miss/replacement/coherency
    ├── test_pipeline_e2e.py   # Full programs: factorial, sort, memcpy
    └── test_spike_compare.py  # Random program vs Spike
```

### Estimated Test Count: ~80

| Test Category | Count | Coverage |
|---------------|:-----:|----------|
| Unit (per module) | 40 | Module-level correctness |
| Pipeline hazard | 10 | Hazard sequences + forwarding |
| Golden vs RTL | 15 | Bit-exact instruction comparison |
| Spike comparison | 10 | Random program comparison |
| Edge cases | 5 | Special values, corner cases |

---

## 7. Synthesis & Physical Design

### Target Constraints

| Parameter | Target |
|-----------|--------|
| Clock frequency | 500 MHz |
| Clock period | 2,000 ps |
| Setup slack | ≥ +200 ps |
| Hold slack | ≥ +50 ps (no negative!) |
| Gate count | ≤ 50K |
| Core area | ~0.1 mm² |
| Target library | ASAP7 (7nm) |

### Synthesis Flow

```bash
yosys -s synth/elaborate.ys   # Elaboration + latch check
yosys -s synth/area.ys        # Per-module generic gate count
```

### Unique Physical Challenges

1. **Clock distribution** — Global clock tree for 500 MHz on a small core. No traveling clock needed (unlike PtahCore's large array).
2. **Register file** — 32×32 register file is tiny but timing-critical. Must floorplan close to decode stage.
3. **Area/power** — Small enough that synthesis should close easily. Main constraint is hold fixing.

---

## 8. Comparison with Prior Art

| Design | ISA | Pipeline | Mul/Div | Frequency | Area | Verification |
|--------|:---:|:--------:|:-------:|:---------:|:----:|:------------|
| picorv32 | RV32IM | 2-stage | Iterative | 200 MHz | ~5K gates | Manual tests |
| SERV | RV32I | Bit-serial | No | 50 MHz | ~1K gates | Formal |
| VexRiscv | RV32IM | 5-stage | Pipelined | 300 MHz | ~15K gates | riscv-tests |
| **SethCore** | **RV32IM** | **5-stage** | **Pipelined** | **500 MHz** | **~50K** | **Bit-exact vs Spike** |
| Rocket | RV64GC | 5-stage | Pipelined | 1 GHz | ~100K | Formal + tests |

SethCore targets the sweet spot between **VexRiscv** (small, no GDSII) and **Rocket** (large, complex). The focus is on clean bit-exact verification and actual GDSII output.

---

## 9. Project-Specific Risks

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Pipeline hazard logic has subtle bug | Medium | High | Formal verification of hazard unit using constrained random |
| Spike compatibility is hard to achieve | Low | Medium | Test against riscv-tests suite early |
| Divider is slow (34 cycles) | Medium | Low | Acceptable for M extension; optimize if needed |
| 500 MHz is aggressive for ASAP7 | Medium | Medium | Target 500 MHz but accept 400 MHz minimum; margin-driven P&R |

---

## 10. Checkpoints

| # | Checkpoint | Deliverable | Verification |
|:-:|------------|-------------|--------------|
| S.1 | Golden ISA simulator complete | golden/ with all instructions | Spike comparison matrix |
| S.2 | pymodel pipeline complete | pymodel/ with 5-stage | Golden-identical output |
| S.3 | All RTL modules written | rtl/ with all .sv files | Individual cocotb tests |
| S.4 | Full pipeline test passes | chip_top testbench | Random program via Spike |
| S.5 | Synthesis clean | No latches, gate count OK | Yosys report |
| S.6 | P&R complete | GDSII, DRC clean | OpenROAD signoff |
| S.7 | CI pipeline | GitHub Actions | All tests on push |

---

## 11. Core Instructions (RV32I)

| Category | Instructions |
|----------|-------------|
| **Arithmetic** | ADD, ADDI, SUB, LUI, AUIPC |
| **Logical** | AND, ANDI, OR, ORI, XOR, XORI |
| **Shift** | SLL, SLLI, SRL, SRLI, SRA, SRAI |
| **Comparison** | SLT, SLTI, SLTU, SLTIU |
| **Branch** | BEQ, BNE, BLT, BGE, BLTU, BGEU |
| **Jump** | JAL, JALR |
| **Load** | LB, LH, LW, LBU, LHU |
| **Store** | SB, SH, SW |
| **Sync** | FENCE, FENCE.I, ECALL, EBREAK |
| **CSR** | CSRRW, CSRRS, CSRRC, CSRRWI, CSRRSI, CSRRCI |

### M Extension

| Instruction | Cycles | Description |
|-------------|:------:|-------------|
| MUL | 4 | Lower 32 bits of product |
| MULH | 4 | Upper 32 bits (signed×signed) |
| MULHU | 4 | Upper 32 bits (unsigned×unsigned) |
| MULHSU | 4 | Upper 32 bits (signed×unsigned) |
| DIV | 34 | Signed quotient |
| DIVU | 34 | Unsigned quotient |
| REM | 34 | Signed remainder |
| REMU | 34 | Unsigned remainder |

---

## 12. Deliverables Summary

| Artifact | Count | Location |
|----------|:-----:|----------|
| Architecture docs | 1 | `docs/01_SethCore_RV32IM_CPU.md` |
| Golden test files | ~6 | `golden/` |
| Golden test cases | ~15 | `golden/tests/` |
| pymodel modules | ~6 | `pymodel/` |
| pymodel tests | ~15 | `pymodel/tests/` |
| RTL modules | ~25 | `rtl/` |
| RTL cocotb tests | ~50 | `rtl/tb/` |
| Synthesis scripts | 2 | `synth/` |
| P&R scripts | 5+ | `flow/` |

---

*Next: [PtahConv — Direct Convolution Accelerator](02_PtahConv_Convolution.md)*
