# 🏛️ RaCore — Heterogeneous AI SoC

> **Deity:** Ra (supreme creator god of Egyptian mythology)
> **Complexity:** ★★★★★
> **Area:** ~3.5 mm² (Lite) / ~16 mm² (Full)

---

## Overview

RaCore is the KemetCore capstone — a heterogeneous AI SoC that integrates all 11 cores over a shared NoC interconnect. It adds three things no single core has:

1. **KAI (Kemet Accelerator Interface)** — one register + DMA contract every core implements, so blocks drop in with zero glue
2. **A real interconnect + memory hierarchy** — NoC, banked scratchpad, descriptor DMA
3. **A post-quantum security enclave** — AnubisCore + NeithCore compose into secure boot + attestation

---

## SoC Architecture

```
                      ┌──────────── RaCore SoC ───────────┐
                      │                                   │
   CPU complex ──▶    │  SethCore (RV32IM) + AtumCore     │
                      │         (RVV vector)               │
                      │              │                      │
                      │      ┌───────▼────────┐             │
   shared fabric ─▶   │      │  KAI NoC + DMA  │             │
                      │      └───────┬────────┘             │
                      │   ┌─────────┼─────────┐            │
   ML cluster ──▶     │ PtahCore Bast PtahConv │ SobekCore  │
                      │ (FP8) (BF16)(conv)     │  (gfx)     │
                      │      GebCore ImentetCore│            │
                      │      (sparse) (attn)    │            │
                      │              │                      │
   security ──▶       │ AnubisCore + NeithCore              │
                      │   = PQ root of trust                │
   shared math ─▶     │ HapiCore (used everywhere)          │
                      └────────────────────────────────────┘
```

---

## Two Tiers

### RaCore-Lite (~3.5 mm²)
- Hierarchical macro-abutment
- Closes on a 16 GB laptop
- **The real deliverable** — shippable to any small fab
- Includes: SethCore, 2-3 ML cores, AnubisCore, HapiCore

### RaCore-Full (~16 mm²)
- All 11 cores on one die
- Real shuttle target
- Requires ≥64 GB for P&R

---

## KAI Interface

Every KemetCore block implements:
- **Register interface:** Command/Status CSRs (AXI4-lite)
- **DMA interface:** Scatter-gather descriptor DMA
- **Interrupt:** Completion notification
- **Conformance test:** `test_kai_conformance` in CI

This means one host driver drives all cores. Integration cost is O(blocks), not O(gates).

---

## Memory Hierarchy

```
DDR (external) ←→ DMA Engine ←→ Banked Scratchpad (256 KiB × 4 banks)
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                          SethCore   AtumCore   ML Cluster
                          (I$/D$)   (vregs)    (SMEM/TMEM)
```

---

## Current RTL (shipping)

| Module | Description |
|--------|-------------|
| `ra_kai_regs` | KAI-compliant register block |
| `ra_noc_arbiter` | Round-robin NoC arbiter |
| `ra_dma` | Descriptor DMA engine |
| `ra_kai_dma` | KAI-compliant DMA accelerator |

---

## Capstone Demo Goal

End-to-end CNN inference + post-quantum attestation on RaCore-Lite:
1. Load weights via DMA
2. SethCore issues commands via KAI
3. ML cluster runs inference (conv + attention)
4. AnubisCore + NeithCore attest the result
5. Read output via DMA
