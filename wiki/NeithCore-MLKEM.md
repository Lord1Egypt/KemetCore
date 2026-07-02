# 🔐 NeithCore — ML-KEM Post-Quantum KEM

> **Deity:** Neith (goddess of war, wisdom, and weaving — fitting for the "woven" lattice structure)
> **Complexity:** ★★★★☆
> **Gates:** ~100K | **Fmax:** 200 MHz | **Area:** ~0.3 mm²

---

## Overview

NIST-standardized post-quantum key encapsulation (FIPS 203, formerly CRYSTALS-Kyber) in hardware. Implements KeyGen, Encaps, and Decaps with an optimized NTT engine for polynomial multiplication over the ring Z_q[x]/(x²⁵⁶+1) where q = 3329.

---

## ML-KEM Parameters

| Parameter | ML-KEM-512 | ML-KEM-768 | ML-KEM-1024 |
|-----------|:----------:|:----------:|:-----------:|
| Security | 128-bit | 192-bit | 256-bit |
| k (dimension) | 2 | 3 | 4 |
| η₁ , η₂ | 3, 2 | 2, 2 | 2, 2 |
| Public key | 800 B | 1,184 B | 1,568 B |
| Ciphertext | 768 B | 1,088 B | 1,568 B |

---

## Architecture

```
DMA Interface
     │
┌────┴──────────────────┐
│ KeyGen │ Encaps │ Decaps │  ← Operation FSMs
└────┬──────────────────┘
     │
┌────▼────┐  ┌──────▼──────┐  ┌─────▼─────┐
│ NTT     │  │ Polynomial  │  │ Sampler   │
│ Engine  │  │ Multiplier  │  │ (CBD+PRF) │
└─────────┘  └─────────────┘  └───────────┘
```

The NTT engine uses a pipelined radix-2 butterfly with Barrett reduction for modular arithmetic.

---

## Current RTL (actively shipping)

| Module | Function |
|--------|----------|
| `neith_polyaddsub` | Polynomial coefficient-wise add/sub mod q |
| `neith_pointwise` | NTT-domain pointwise multiply |
| `neith_polymul` | Full negacyclic polynomial multiply |
| `neith_cbd` | Centered binomial distribution noise sampler |
| `neith_msgcodec` | Message ↔ polynomial encoding |

---

## Why Hardware for ML-KEM?

| Metric | Software (AVX2) | NeithCore (est.) |
|--------|:---------------:|:----------------:|
| KeyGen | ~25K cycles | ~5K cycles |
| Encaps | ~30K cycles | ~6K cycles |
| Decaps | ~35K cycles | ~7K cycles |
| Power | ~15W (CPU) | ~0.5W (ASIC) |

---

## Role in RaCore

Together with AnubisCore (for SHAKE-256), NeithCore forms the **post-quantum root of trust** for the RaCore SoC — secure boot and attestation resistant to quantum attacks.
