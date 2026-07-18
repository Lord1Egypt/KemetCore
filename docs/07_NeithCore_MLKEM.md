# 𓋇 NeithCore — Kyber-round-1-style Lattice/NTT Accelerator (Q=7681)

> **Deity:** Neith (𓋇, goddess of war, wisdom, and weaving — fitting for the "woven" structure of lattice crypto)
> **Domain:** Kyber-round-1-style lattice/NTT engine (Q=7681)
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 200 MHz on ASAP7
> **Est. Gates:** ~100K (largest crypto project)
> **Complexity:** ★★★★☆

---

## 1. Technical Overview

### A Note on Standards and Scope
NeithCore implements the mathematics of Kyber round 1 using a modulus of Q=7681. FIPS-203 (ML-KEM) uses a modulus of q=3329. Therefore, NeithCore will not pass FIPS-203 KAT vectors, but serves as a representative lattice/NTT hardware engine.

### Constant-Time Security
NeithCore datapaths are fixed-latency by construction (no secret-dependent branches or memory addressing). Masking/DPA resistance is a non-goal for this phase.

NeithCore is a dedicated hardware accelerator for lattice operations. It implements KeyGen, Encaps, and Decaps operations with an optimized NTT (Number Theoretic Transform) engine for polynomial multiplication.

### Why ML-KEM Hardware?

| Metric | Software (Reference) | Software (Optimized AVX2) | NeithCore (Estimated) |
|--------|:--------------------:|:-------------------------:|:---------------------:|
| KeyGen | ~100K cycles | ~25K cycles | ~5K cycles |
| Encaps | ~120K cycles | ~30K cycles | ~6K cycles |
| Decaps | ~140K cycles | ~35K cycles | ~7K cycles |
| Power | ~15W (CPU) | ~15W (CPU) | ~0.5W (ASIC) |

### ML-KEM Parameters

| Parameter | ML-KEM-512 | ML-KEM-768 | ML-KEM-1024 |
|-----------|:----------:|:----------:|:-----------:|
| Security level | 128-bit | 192-bit | 256-bit |
| k (NTT size) | 2 | 3 | 4 |
| η₁, η₂ | 3, 2 | 2, 2 | 2, 2 |
| d_u, d_v | 10, 4 | 10, 4 | 11, 5 |
| Public key size | 800 B | 1,184 B | 1,568 B |
| Secret key size | 1,632 B | 2,400 B | 3,168 B |
| Ciphertext size | 768 B | 1,088 B | 1,568 B |

---

## 2. Architecture

### Top-Level Datapath

```
┌─────────────────────────────────────────────────────┐
│                     DMA Interface                    │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
     ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
     │   KeyGen  │  │  Encaps   │  │  Decaps   │
     │   FSM     │  │   FSM     │  │   FSM     │
     └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                    ┌─────▼─────┐
                    │   NTT     │
                    │   Engine  │
                    │ (butterfly)│
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │ Polynomial │
                    │ Multiplier │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │   Sampler │
                    │ (CBD + PRF)│
                    └───────────┘
```

### Module Hierarchy

```
neithcore/
├── neith_top.sv               # Top-level + mode selection
├── neith_keygen.sv            # KeyGen FSM
├── neith_encaps.sv            # Encaps FSM
├── neith_decaps.sv            # Decaps FSM
├── neith_ntt.sv               # NTT forward transform
├── neith_intt.sv              # Inverse NTT
├── neith_butterfly.sv         # Single butterfly unit
├── neith_poly_mul.sv          # Polynomial multiplication
├── neith_sampler.sv           # CBD + PRF (SHAKE-256)
├── neith_compress.sv          # Coefficient compression
├── neith_decompress.sv        # Coefficient decompression
├── neith_encode.sv            # Byte ↔ polynomial encoding
├── neith_decode.sv            # Polynomial ↔ byte decoding
├── neith_shake.sv             # SHAKE-256 core (from AnubisCore)
├── neith_mem.sv               # Internal coefficient memory
└── neith_controller.sv        # Main control FSM
```

### NTT Butterfly

```
a ──▶┌──────────────────────────────────────────┐
     │  ntt_butterfly.sv                        │
b ──▶│                                          │──▶ a' = a + ζ×b
     │  a' = a + (ζ × b) mod q                  │
     │  b' = a − (ζ × b) mod q                  │──▶ b' = a − ζ×b
     │  where q = 3329, ζ is the twiddle factor  │
     └──────────────────────────────────────────┘
```

The NTT engine uses a **pipelined radix-2** butterfly with:
- Modular multiplication: Barrett or Montgomery reduction
- Configurable twiddle factor ROM
- 8→64→256-point NTT (iterated)

---

## 3. Golden Reference

```
golden/
├── ml_kem.py                  # Full ML-KEM implementation (numpy)
├── ntt.py                     # NTT/INTT reference
├── poly_mul.py                # Polynomial multiplication (schoolbook + NTT)
├── sampler.py                 # CBD + PRF sampling
├── compress.py                # Coefficient compression/decompression
├── shake.py                   # SHAKE-256 (wrapping hashlib)
├── fips_203_vectors.py        # NIST FIPS 203 known-answer tests
└── tests/
    ├── test_ml_kem.py         # KeyGen→Encaps→Decaps roundtrip (100×)
    ├── test_ntt.py            # NTT(INTT(x)) == x for all values
    ├── test_sampler.py        # CBD distribution matches spec
    ├── test_compress.py       # Roundtrip error bound ≤ spec
    └── test_fips_203.py       # Known-answer test vectors
```

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: roundtrip | 10 | KeyGen→Encaps→Decaps roundtrip |
| Golden: NTT invertibility | 6 | NTT(INTT(x)) = x for various polynomials |
| Golden: FIPS 203 KATs | 10 | NIST known-answer tests (all 3 parameter sets) |
| pymodel: butterfly | 6 | Correctness at all pipeline stages |
| pymodel: FSM | 4 | KeyGen/Encaps/Decaps state transitions |
| RTL: butterfly | 6 | All ζ values, boundary cases (q-1, 0) |
| RTL: NTT engine | 6 | 256-point NTT × random polynomials |
| RTL: sampler | 4 | CBD distribution statistical check |
| RTL: full chip | 6 | Roundtrip: all 3 parameter sets |
| **Total** | **~58** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| AnubisCore | SHAKE-256 core (shared) | [docs/06_AnubisCore_HashEngine.md](06_AnubisCore_HashEngine.md) |
| HapiCore | FP32 (not used here; all integer) | N/A |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| Clock | 200 MHz |
| NTT width | 256-point (k=4 for ML-KEM-1024) |
| Butterfly units | 2 (parallel) |
| NTT cycles | ~256 per transform |
| KeyGen cycles | ~5K |
| Encaps cycles | ~6K |
| Decaps cycles | ~7K |
| Area | ~0.3 mm² |
| Coefficient memory | 3,072 × 16-bit = ~6 KiB |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| NE.1 | Golden: ML-KEM | FIPS 203 KATs pass |
| NE.2 | Golden: NTT | Invertibility verified |
| NE.3 | Golden: roundtrip | 100× random roundtrip |
| NE.4 | pymodel: butterfly + NTT | Cycle-level, pipelined |
| NE.5 | pymodel: full chip | All 3 parameter sets |
| NE.6 | RTL: butterfly | Single butterfly, all ζ |
| NE.7 | RTL: NTT engine | 256-point NTT correct |
| NE.8 | RTL: sampler | CBD + PRF correct |
| NE.9 | RTL: full chip | KeyGen→Encaps→Decaps |
| NE.10 | Synthesis | ≤ 150K gates |
| NE.11 | P&R | DRC clean |

---

## 8. Comparison with Prior Art

| Design | Platform | ML-KEM | NTT Cycles | Area |
|--------|----------|:------:|:----------:|:----:|
| **NeithCore** | **ASAP7 (7nm)** | **All** | **256** | **0.3 mm²** |
| pqm4 (software) | Cortex-M4 | 768 | N/A (SW) | N/A |
| Kyber-LW (FPGA) | Artix-7 | 768 | 512 | ~5K LUTs |
| HWKyber (ASIC) | 28nm | 768 | 256 | 0.5 mm² |
| Google (FPGA) | Stratix 10 | All | 128 | ~10K ALMs |

NeithCore targets ~2× better area efficiency than comparable ASIC designs by using an optimized single-butterfly datapath with high utilization.

---

*Prev: [AnubisCore](06_AnubisCore_HashEngine.md) · Next: [SobekCore — Ray-Trace](08_SobekCore_RayTrace.md)*
