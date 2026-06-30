# ⚡ AnubisCore — SHA-256/SHA-3 Hash Engine

> **Deity:** Anubis (god of embalming — fitting for a hash that "digests" data)
> **Complexity:** ★★☆☆☆
> **Gates:** ~15K | **Fmax:** 1 GHz | **Area:** ~0.05 mm²

---

## Overview

The most complete KemetCore block — **Phase 2 RTL is DONE and synthesis reports exist.** A unified hardware accelerator for SHA-256, SHA-224, SHA-384, SHA-512, SHA3-256, SHA3-384, and SHA3-512 with automatic message padding and mode selection.

---

## Architecture

```
input data (512-bit blocks)
     │
     ▼
┌─────────────────────────┐
│     PADDING UNIT        │ ← appends 0x80, 0x00..., bit-length
│  (shared for all modes) │
└─────────┬───────────────┘
          │
          ├──▶ SHA-256 Path ──▶ Message Schedule (W_0..W_63) ──▶ Compression (Σ0, Σ1, Maj, Ch)
          │                                                     state (8×32-bit)
          │
          ├──▶ SHA-512 Path ──▶ Message Schedule (W_0..W_79) ──▶ Compression (64-bit state)
          │
          ├──▶ SHA-3 Path  ──▶ Keccak-f[1600] (θ, ρ, π, χ, ι) ──▶ 5×5×64-bit state
          │
          └──▶ OUTPUT ──▶ Digest register (224/256/384/512 bits)
```

---

## Supported Algorithms

| Algorithm | Digest Size | Block | Rounds | Standard |
|-----------|:-----------:|:-----:|:------:|----------|
| SHA-224 | 224 bits | 512 | 64 | FIPS 180-4 |
| SHA-256 | 256 bits | 512 | 64 | FIPS 180-4 |
| SHA-384 | 384 bits | 1024 | 80 | FIPS 180-4 |
| SHA-512 | 512 bits | 1024 | 80 | FIPS 180-4 |
| SHA3-224 | 224 bits | 1152 | 24 | FIPS 202 |
| SHA3-256 | 256 bits | 1088 | 24 | FIPS 202 |
| SHA3-384 | 384 bits | 832 | 24 | FIPS 202 |
| SHA3-512 | 512 bits | 576 | 24 | FIPS 202 |

---

## Module Hierarchy

| Module | Description |
|--------|-------------|
| `anubis_top` | Top-level + mode selection |
| `anubis_padder` | Message padding (shared) |
| `sha256_core` | SHA-256 full datapath |
| `sha512_core` | SHA-512 full datapath |
| `sha3_256_core` | SHA3-256 (Keccak-f) |
| `sha3_384_core` | SHA3-384 |
| `sha3_512_core` | SHA3-512 |
| `anubis_keccak_round` | Single Keccak round (θ, ρ, π, χ, ι) |
| `anubis_controller` | Main FSM (absorb → process → squeeze) |

---

## Synthesis Results

**Status:** 🔧 Synthesis reports exist for `sha256_core` and `sha3_256_core`.  
**Target:** 1 GHz on ASAP7 7nm PDK.

---

## Why 1 GHz?

Crypto is embarrassingly serial — no parallelism possible. The only way to go fast is clock speed. At 1 GHz:
- SHA-256: ~1.6 Gbps (512 bits × 1 GHz / 64 rounds / ~5 cycles overhead)
- SHA-3-256: ~5.4 Gbps (1088 bits × 1 GHz / 24 rounds / ~8 cycles overhead)

---

## Verification

Uses full NIST test vectors + random fuzzing:
- **Golden:** Bit-exact vs Python hashlib
- **pymodel:** Cycle-level FSM vs golden
- **RTL:** cocotb tests comparing against pymodel output
- **Synthesis:** Yosys elaboration, 0 latches enforced
