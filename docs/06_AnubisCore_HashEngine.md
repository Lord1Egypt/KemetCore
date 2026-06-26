# 𓇋𓈖𓃀𓅱𓃭 AnubisCore — SHA-256/SHA-3 Cryptographic Hash Engine

> **Deity:** Anubis (𓇋𓈖𓃀𓅱𓃭, god of embalming and the afterlife — fitting for a hash function that "digests" data)
> **Domain:** Cryptography
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 1 GHz on ASAP7
> **Est. Gates:** ~15K
> **Complexity:** ★★☆☆☆

---

## 1. Technical Overview

AnubisCore is a **cryptographic hash hardware accelerator** supporting both SHA-256 and SHA-3 (Keccak) algorithms. It provides a unified frontend that selects between the two hash modes, handles message padding automatically, and computes the full hash digest in hardware.

### Why Hash Hardware?

| Use Case | Why Hardware? |
|----------|---------------|
| Blockchain (Maat) | Block headers require double-SHA256 for proof-of-work |
| Merkle tree verification | ~log N hashes per verification (I/O bound in software) |
| Post-quantum crypto | ML-KEM/ML-DSA sign/verify requires hashing |
| Disk/storage integrity | Checksumming at memory bandwidth (SW can't match) |

### Supported Algorithms

| Algorithm | Digest Size | Block Size | Rounds | Standard |
|-----------|:-----------:|:----------:|:------:|----------|
| SHA-256 | 256 bits | 512 bits | 64 | FIPS 180-4 |
| SHA-3-256 | 256 bits | 1,088 bits | 24 | FIPS 202 |
| SHA-3-512 | 512 bits | 832 bits | 24 | FIPS 202 |

---

## 2. Architecture

### Unified Datapath

```
input data (512-bit blocks)
     │
     ▼
┌─────────────────────────┐
│     PADDING UNIT        │ ← appends 0x80, 0x00..., bit-length
│  (shared SHA-256/SHA-3) │
└─────────┬───────────────┘
          │
          ├──▶ SHA-256 Path ──▶ Message Schedule (Wt.0..63) ──▶ Compression (Σ0, Σ1, Maj, Ch)
          │                                                     │
          │                                                    state (8×32-bit)
          │                                                     │
          ├──▶ SHA-3 Path  ──▶ Keccak-f[1600] (θ, ρ, π, χ, ι) ──▶ 5×5×64-bit state
          │
          └──▶ OUTPUT ──▶ Digest register (256 or 512 bits)
```

### Module Hierarchy

```
anubiscore/
├── anubis_top.sv              # Top-level + mode selection
├── anubis_padder.sv           # Message padding (shared)
├── anubis_sha256.sv           # SHA-256 top
├── anubis_sha256_schedule.sv  # Message schedule (W_0..W_63)
├── anubis_sha256_round.sv     # Single round (σ0, σ1, Maj, Ch, Σ0, Σ1)
├── anubis_sha256_state.sv     # 8×32-bit working state
├── anubis_sha3.sv             # SHA-3 top
├── anubis_keccak_round.sv     # Single Keccak round (θ, ρ, π, χ, ι)
├── anubis_keccak_state.sv     # 5×5×64-bit state + RC constant
├── anubis_rate_buffer.sv      # Absorb/squeeze rate buffer
├── anubis_controller.sv       # Main FSM (absorb → process → squeeze)
└── anubis_output.sv           # Digest output alignment
```

### SHA-256 Datapath

```
W_0..W_15 ──▶ Schedule expansion (W_t = σ1(W_{t-2}) + W_{t-7} + σ0(W_{t-15}) + W_{t-16})
                    │
                    ▼
a,b,c,d,e,f,g,h ◀──▶ Round function (64 iterations)
     │                  │
     └──────────────────┘
     8×32-bit registers updated per round

Round function per iteration:
    T1 = h + Σ1(e) + Ch(e,f,g) + K_t + W_t
    T2 = Σ0(a) + Maj(a,b,c)
    h, g, f, e = g, f, e, d + T1
    d, c, b, a = c, b, a, T1 + T2
```

### SHA-3 (Keccak-f[1600]) Datapath

```
State: 5×5 lanes × 64 bits = 1,600 bits

Round function (24 iterations):
    θ:  C[x] = XOR(A[x,0..4])
        D[x] = C[x-1] XOR ROT(C[x+1], 1)
        A[x,y] = A[x,y] XOR D[x]

    ρ:  A[0,0] = A[0,0]               (no rotation)
        A[x,y] = ROT(A[x,y], offsets)

    π:  B[y, 2x+3y] = A[x,y]

    χ:  A[x,y] = B[x,y] XOR ((NOT B[x+1,y]) AND B[x+2,y])

    ι:  A[0,0] = A[0,0] XOR RC[round]
```

---

## 3. Golden Reference

```
golden/
├── sha256.py                  # Pure Python SHA-256
├── sha3.py                    # Pure Python SHA-3 (Keccak-f[1600])
├── nist_vectors.py            # NIST test vectors (CAVP format)
└── tests/
    ├── test_sha256.py         # NIST vectors: 0-bit, 1-bit, repeated, random
    ├── test_sha3.py           # NIST vectors: all variants
    ├── test_padding.py        # Padding correctness (empty, aligned, unaligned)
    └── test_streaming.py      # Streaming: absorb bytes→hash vs one-shot
```

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: SHA-256 NIST | 10 | 0-bit, 1-bit, 1-byte, random, edge |
| Golden: SHA-3 NIST | 10 | All 4 variants (224/256/384/512) |
| pymodel: padding | 4 | All alignment cases |
| pymodel: streaming | 4 | Multi-block absorption |
| RTL: SHA-256 rounds | 4 | State transitions for known inputs |
| RTL: SHA-3 Keccak | 4 | θ/ρ/π/χ/ι correctness |
| RTL: full digest | 6 | NIST vectors: all modes |
| **Total** | **~42** | |

---

## 5. Performance Targets

| Metric | SHA-256 | SHA-3-256 | SHA-3-512 |
|--------|:-------:|:---------:|:---------:|
| Clock | 1 GHz | 1 GHz | 1 GHz |
| Cycles/block | 64 (unrolled) | 24 (unrolled) | 24 |
| Throughput | 8 GB/s | 45 GB/s | 35 GB/s |
| Latency | 64 ns | 24 ns | 24 ns |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| Clock | 1 GHz (fastest of all KemetCore projects) |
| Gates | ~15K |
| Area | ~0.05 mm² |
| Critical path | SHA-256 Σ0/Σ1 XOR tree |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| AN.1 | Golden: SHA-256 | Matches hashlib.sha256 |
| AN.2 | Golden: SHA-3 | Matches hashlib.sha3_256 |
| AN.3 | Golden: NIST vectors | All pass |
| AN.4 | pymodel: both paths | Cycle-level |
| AN.5 | RTL: SHA-256 path | NIST vectors pass |
| AN.6 | RTL: SHA-3 path | NIST vectors pass |
| AN.7 | RTL: shared padder | Correct padding |
| AN.8 | RTL: full chip | All modes pass |
| AN.9 | Synthesis | 0 latches, ≤ 20K gates |
| AN.10 | P&R at 1 GHz | DRC clean |

---

*Prev: [BastCore](05_BastCore_BF16Tensor.md) · Next: [NeithCore — ML-KEM](07_NeithCore_MLKEM.md)*
