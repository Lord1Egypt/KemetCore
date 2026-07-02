# 🧠 GebCore — 2:4 Sparse Matmul

> **Deity:** Geb (god of the earth — sparsity lives in the "ground" of the weight matrix)
> **Complexity:** ★★★☆☆
> **Gates:** ~4M | **Fmax:** 250 MHz | **Area:** ~2 mm²

---

## Overview

2:4 structured sparse matmul — the same compute primitive as NVIDIA Ampere/Hopper/Blackwell sparse tensor cores. Every contiguous 4-weight group has exactly 2 non-zeros, with positions stored as 2-bit metadata.

---

## The Magic of 2:4

```
Dense:   [a0, a1, a2, a3, a4, a5, a6, a7, ...]   ← 100% weights
Sparse:  [a0, a1,        a4,       a7, ...]       ← 50% weights
Meta:    [00,             01,       10]            ← 2 bits per group

Storage: 18 bits/group vs 32 dense → 44% compression
Throughput: 2× MACs active vs dense
Accuracy loss: ~0% (proven in production LLMs)
```

---

## Architecture

| Operand A | Operand B | MACs Active | Throughput |
|-----------|-----------|:-----------:|:----------:|
| Dense | Dense | 16 (fallback) | 1× |
| Dense | 2:4 Sparse | 32 | 2× |
| 2:4 Sparse | Dense | 32 | 2× |
| 2:4 Sparse | 2:4 Sparse | 32 | 2× |

Transparent fallback: if no sparsity detected, operates at full accuracy with dense mode.
