# 🏛️ SethCore — RISC-V RV32IM Pipelined CPU

> **Deity:** Seth (god of chaos, strength, and the desert)
> **Complexity:** ★★★★☆
> **Gates:** ~50K | **Fmax:** 500 MHz | **Area:** ~0.1 mm²

---

## Overview

A 5-stage in-order pipelined RISC-V CPU implementing RV32IM + Zicsr + Zifencei. Classic Harvard microarchitecture with full data forwarding, 2-bit branch predictor + BTB, pipelined 4-cycle multiply, and 34-cycle non-restoring signed divide.

---

## Pipeline

```
FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK
  │        │         │         │          │
  └────────┴───forwarding paths───────────┘
```

| Stage | What Happens |
|-------|-------------|
| **FETCH** | PC+4, I-cache lookup, branch prediction |
| **DECODE** | Register file read (3R1W), immediate generation, hazard detection |
| **EXECUTE** | ALU op, MUL op (pipelined), DIV op, address generation |
| **MEMORY** | D-cache access, load/store unit |
| **WRITEBACK** | Register file write, forwarding muxes |

---

## Hazard Handling

| Hazard | Strategy |
|--------|----------|
| RAW (read-after-write) | Full forwarding from E, M, W stages; stall if load-use |
| WAW/WAR | Impossible — single write port, in-order |
| Control (branches) | 2-bit predictor + BTB; 2-cycle mispredict penalty |
| Structural (regfile) | 3-read 1-write; no structural stalls |

---

## Verification

Bit-exact vs **Spike** (the RISC-V golden reference simulator). Every instruction execution is compared byte-for-byte against Spike's output over the RISC-V test vector suite (riscv-tests).

---

## Features vs Typical Teaching Cores

| Feature | SethCore | picorv32 / SERV |
|---------|:--------:|:----------------:|
| Pipeline | 5-stage | 2-3 stage or state machine |
| Multiply | Pipelined 4-cycle | Iterative (32+ cycles) |
| Divide | Non-restoring 34-cycle | Not implemented |
| Forwarding | Full forwarding network | None (stall everything) |
| Branch Predictor | 2-bit + BTB | Always not-taken |
| Verification | Bit-exact vs Spike | Manual inspection |
