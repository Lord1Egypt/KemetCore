# 🏛️ Architecture Overview

## The Big Picture — RaCore SoC

```
                      ┌──────────── RaCore SoC (capstone) ───────────┐
                      │                                              │
   CPU complex ──▶    │  SethCore (RV32IM) + AtumCore (RVV vector)   │
                      │                    │                          │
                      │            ┌───────▼────────┐                 │
   shared fabric ─▶   │            │  KAI NoC + DMA  │                 │
                      │            └───────┬────────┘                 │
                      │     ┌──────────────┼───────────────┐          │
   ML cluster ──▶     │  PtahCore Bast PtahConv Geb Imentet │  Sobek   │
                      │  (FP8) (BF16)(conv)(sparse)(attn)   │  (gfx)   │
                      │                    │                          │
   security ──▶       │  AnubisCore + NeithCore = PQ root of trust    │
   shared math ─▶     │  HapiCore (FPU library, used everywhere)      │
                      └──────────────────────────────────────────────┘
```

Every block speaks **KAI (Kemet Accelerator Interface)** — a common register + DMA contract that makes integration cost scale with the number of blocks, not the number of gates.

---

## KAI — Kemet Accelerator Interface

Every core implements:
- **1 register map interface** — CSRs for command/status
- **1 DMA descriptor interface** — scatter-gather DMA engine
- **1 interrupt line** — completion notification
- **1 `test_kai_conformance` check** — set in CI for every block

This means: one host driver, one testbench skeleton, one conformance suite → all 11 cores.

---

## Dependency Graph

```
HapiCore, AnubisCore           (no deps — build first)
  → BastCore, SethCore         (need HapiCore)
    → PtahConv, GebCore        (need BastCore)
      → ImentetCore            (needs PtahConv + GebCore)
SobekCore, NeithCore           (independent)
AtumCore                       (needs SethCore + HapiCore)
  → RaCore (capstone)          (needs ALL, KAI-conformant)
```

---

## Two Tiers

| Tier | Area | Target | Feasibility |
|------|:----:|--------|:-----------:|
| **RaCore-Lite** | ~3.5 mm² | GDSII on a 16 GB laptop | ✅ Hierarchical macro-abutment |
| **RaCore-Full** | ~16 mm² | Real shuttle target | Real iron required (≥64 GB) |

---

## Memory Hierarchy

```
DDR (external) ←→ DMA Engine ←→ Banked Scratchpad ←→ Cores
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                          SethCore   AtumCore   ML Cluster
                          (I$/D$)   (vregs)    (SMEM/TMEM)
```

---

## Clock Domains

| Domain | Frequency | Blocks |
|--------|:---------:|--------|
| CPU | 500 MHz | SethCore, AtumCore |
| ML | 250 MHz | PtahConv, GebCore, ImentetCore, BastCore |
| Crypto | 1 GHz | AnubisCore |
| Crypto-slow | 200 MHz | NeithCore |
| Graphics | 500 MHz | SobekCore |
| Math | 500 MHz | HapiCore |

Async FIFOs at all domain boundaries with CDC lint checks.
