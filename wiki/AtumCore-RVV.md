# 🧮 AtumCore — RISC-V Vector Extension Unit

> **Deity:** Atum (the creator god — synthesized all the others into being, just as vector processing synthesizes scalar ops into parallel computation)
> **Complexity:** ★★★★★
> **Gates:** ~100K+ | **Fmax:** 500 MHz | **Area:** ~0.5 mm²

---

## Overview

The largest and most complex KemetCore project. A full **RISC-V Vector Extension v1.0** coprocessor that plugs into SethCore to provide vector processing. Implements a decoupled vector execution unit with dedicated vector register file, 8 ALU lanes, and a vector memory unit.

---

## Key Specifications

| Parameter | Target |
|-----------|--------|
| VLEN | 256 bits |
| ELEN | 64 bits |
| LMUL | 1, 2, 4, 8 |
| Vector registers | 32 × 256-bit = 1 KiB |
| Mask registers | 8 × 32-bit = 32 bytes |
| ALU lanes | 8 (32-bit per lane) |
| Pipeline | Decoupled, command-queue driven |

---

## Architecture

```
SethCore ──▶ [Command Queue (8)] ──▶ [Decode + Sequencer]
                                           │
                              ┌────────────┼────────────┐
                              ▼                         ▼
                      [Vector ALU 8 lanes]      [Vector LSU 10 stages]
                              │                         │
                              └────────┬────────────────┘
                                       ▼
                              [Vector Register File 32×256b]
                              [Mask Register File 8×32b]
```

---

## Current RTL (20+ modules shipped!)

| Module | RVV Instruction |
|--------|----------------|
| `atum_vcore` | Top-level + command queue |
| `atum_valu` | Integer arithmetic (vadd, vsub, vand, vor, vxor, vsll, vsrl, vsra) |
| `atum_vmul` | Integer multiply (vmul, vmulh, vmulhu, vmulhsu) |
| `atum_vdiv` | Integer divide/remainder (vdivu, vdiv, vremu, vrem) |
| `atum_vaadd` | Averaging add/sub (vaaddu, vaadd, vasub) |
| `atum_vimac` | Integer multiply-add (vnmsac, vmadd, vnmsub) |
| `atum_vfpu` | FP add/mul/fma (vfadd, vfmul, vfFMA) |
| `atum_vfsqrt` | FP sqrt (vfsqrt.v) |
| `atum_vfdiv` | FP divide (vfdiv, vfrdiv) |
| `atum_vfminmax` | FP min/max (vfmin, vfmax) |
| `atum_vfredsum` | FP reduction sum (vfredosum, vfredusum) |
| `atum_vredminmax` | Integer reduction min/max |
| `atum_vfsgnj` | FP sign injection (vfsgnj/n/x) |
| `atum_vfclass` | FP classify (vfclass) |
| `atum_vcompress` | Stream compaction (vcompress) |
| `atum_vrgather` | Register gather/permute (vrgather) |
| `atum_vslide` | Vector slide (vslideup, vslidedown) |
| `atum_vslide1` | Slide-by-1 (vslide1up, vslide1down) |
| `atum_vmerge` | Masked merge (vmerge) |
| `atum_vmv` | Vector move (vmv.v.x, vmv.v.v, vmv.x.s, vmv.s.x) |
| `atum_vmsbf` | Mask set-before/if/only-first (vmsbf, vmsif, vmsof) |
| `atum_viota` | Index generation (viota, vid) |
| `atum_vmask` | Mask logic (vmand, vmnand, vmor, etc.) |
| `atum_vmpopc` | Mask population count |
| `atum_vmlogic` | Vector mask logical ops |
| `atum_vredu` | Integer reduction (vredsum, vredand, vredor, vredxor) |
| `atum_vregfile` | Vector register file |
| `atum_vsetvl` | Vector length configuration |

---

## RVV v1.0 Instruction Groups

| Group | Status |
|-------|:------:|
| Configuration (vsetvli, vsetvl) | ✅ |
| Unit-stride load/store | ✅ |
| Strided load/store | ⬜ |
| Indexed load/store (scatter/gather) | ⬜ |
| Integer arithmetic | ✅ |
| Integer multiply | ✅ |
| Integer compare | ⬜ |
| Shift/permute | ✅ |
| Floating-point | ✅ |
| Reduction | ✅ |
| Mask logic | ✅ |

---

## Why RVV Length-Agnostic?

AtumCore is designed to the RVV v1.0 spec which is **length-agnostic**: software compiled once runs on any VLEN implementation. This means AtumCore code will run on everything from a 128-bit embedded vector unit to a 65,536-bit HPC vector processor — without recompilation.
