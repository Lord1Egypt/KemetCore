# 🎮 SobekCore — Ray-Triangle Intersector

> **Deity:** Sobek (god of the Nile, crocodiles — ambush predator, like a ray "striking" its target)
> **Complexity:** ★★★☆☆
> **Gates:** ~30K | **Fmax:** 500 MHz | **Area:** ~0.08 mm²

---

## Overview

Hardware ray-triangle intersection unit implementing Möller-Trumbore in a fully pipelined 5-stage datapath. 1 ray vs 1 triangle per cycle. Watertight edge handling.

---

## Pipeline

```
V0,V1,V2,O,D
     │
  [SUB] → E1, E2, T
     │
  [CROSS] → P, Q
     │
  [DOT] → det, T·P, D·Q
     │
  [RECIP] → 1/det (Newton-Raphson)
     │
  [MULT] → t, u, v × inv_det
     │
  [TEST] → hit = u≥0 ∧ v≥0 ∧ u+v≤1 ∧ t∈[min,max]
```

---

## Watertightness

Prevents rays from slipping through shared triangle edges due to FP rounding:
- Edge classification with tie-breaker rule
- Sheared arithmetic (subtract scaled ray direction)
- Double-hit prevention (always report closest hit)

---

## Throughput Comparison

| Engine | Rays/Triangle per cycle |
|--------|:-----------------------:|
| SobekCore | 1 |
| Software (Embree) | ~0.01 (SIMD) |
| NVIDIA RT Core | ~1 (estimated) |
