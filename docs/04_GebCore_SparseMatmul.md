# 𓅬 GebCore — 2:4 Structured Sparse Matmul Accelerator

> **Deity:** Geb (𓅬, god of the earth — because sparsity lives in the "ground" of the weight matrix)
> **Domain:** ML — Structured Sparsity
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 250 MHz on ASAP7
> **Est. Gates:** ~4M
> **Complexity:** ★★★☆☆

---

## 1. Technical Overview

GebCore implements **2:4 structured sparsity** — the same sparse compute primitive used by NVIDIA's Ampere/Hopper/Blackwell architectures. In 2:4 sparsity, every contiguous group of 4 weights contains exactly 2 non-zero values, at fixed positions determined by a 2-bit metadata field.

### Why 2:4 Sparsity?

| Metric | Dense | 2:4 Sparse | Gain |
|--------|:-----:|:----------:|:----:|
| Weights stored | 100% | 50% | 2× reduction |
| MAC throughput | 1× | 2× | 2× |
| Accuracy loss | — | ~0% | Minimal (proven) |
| Additional hardware | None | Metadata decoder + mux | Small overhead |

### Key Innovations

| Feature | GebCore | NVIDIA Sparse Tensor Core |
|---------|---------|---------------------------|
| **Dense-sparse hybrid** | Both matrices can be dense or 2:4 sparse | Fixed (one sparse operand) |
| **FP8 native** | Uses PtahCore's FP8 pipeline | FP16/BF16 |
| **Online pruning** | Optional: detect and skip zeros in dense operand | Sparse-only |
| **Transparent fallback** | Falls back to dense matmul if no sparsity detected | No fallback |

---

## 2. Architecture

### Sparse Encoded Format

```
Dense:  [a0, a1, a2, a3,  a4, a5, a6, a7, ...]
         ↓ prune to 2-of-4, store indices
Sparse: [a0, a1,        a4,       a7, ...]    # non-zero values
Meta:   [00b,           01b,      10b]         # 2 bits per group
```

Each 4-element group becomes:
- 2 non-zero values (FP8: 16 bits)
- 2-bit metadata (which positions are non-zero)
- Total: 18 bits per group (vs 32 bits dense) — **44% compression**

### Sparse MAC Array

```
Dense activation vector (32 elements west→east)
     │
     ▼
┌────────────────────────────────────────┐
│ Sparse Decoder    │     Metadata ROM   │
│ (metadata→mux)   │     (2 bits/group) │
├────────────────────────────────────────┤
│                                        │
│   16 MACs (not 32!) — one per          │
│   non-zero weight in a 4-group pair    │
│                                        │
│   MAC0: activation[meta0] × weight[0]  │
│         +                              │
│   MAC1: activation[meta1] × weight[1]  │
└────────────────────────────────────────┘
```

### Module Hierarchy

```
gebcore/
├── gebcore_top.sv             # Top-level controller
├── gebcore_sparse_encode.sv   # Dense→sparse encoder (for pruning)
├── gebcore_sparse_decode.sv   # Sparse metadata decoder
├── gebcore_mac_sparse.sv      # 2-MAC fused unit (shared mul)
├── gebcore_sparse_row.sv      # Row of sparse MACs
├── gebcore_sparse_grid.sv     # 16×32 sparse grid
├── gebcore_dense_fallback.sv  # Transparent dense mode
├── gebcore_prune_unit.sv      # Online 2:4 pruning unit
└── gebcore_drain.sv           # Output accumulation
```

### Supported Configurations

| Operand A | Operand B | Macs Active | Throughput |
|-----------|-----------|:-----------:|:----------:|
| Dense | Dense | 16 (fallback) | 1× |
| Dense | 2:4 Sparse | 32 (both halves) | 2× |
| 2:4 Sparse | Dense | 32 (both) | 2× |
| 2:4 Sparse | 2:4 Sparse | 32 (all) | 2× |

---

## 3. Golden Reference

```
golden/
├── sparse_matmul.py           # 2:4 sparse matmul golden
├── sparse_encode.py           # Dense → 2:4 encoder
├── sparse_decode.py           # Metadata decoder
├── prune.py                   # 2:4 pruning algorithms (magnitude-based)
├── accuracy_sweep.py          # Accuracy vs dense for known models
└── tests/
    ├── test_sparse_matmul.py  # Bit-exact vs dense at 2:4 positions
    ├── test_encode_decode.py  # Roundtrip: dense→sparse→dense
    ├── test_prune.py          # 2:4 constraint (exactly 2/4)
    └── test_accuracy.py       # Error bound ≤ dense ULP
```

---

## 4. Testing Strategy

| Test Layer | Count | What It Verifies |
|------------|:-----:|------------------|
| Golden: matmul parity | 8 | Random: dense sparse bit-identical |
| Golden: encode/decode | 4 | Roundtrip, boundary cases |
| pymodel: fallback | 3 | Dense fallback matches PtahCore |
| pymodel: throughput | 2 | 2× throughput confirmed |
| RTL: sparse decode | 4 | Metadata → correct activation mux |
| RTL: sparse MAC | 6 | Single MAC: 4×4 group all positions |
| RTL: full array | 6 | 16×32 grid vs golden |
| **Total** | **~33** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| PtahCore | FP8 encode/decode, mac_cell template | [Lord1Egypt/PtahCore](https://github.com/Lord1Egypt/PtahCore) |
| BastCore | BF16 variant (optional) | [docs/05_BastCore_BF16Tensor.md](05_BastCore_BF16Tensor.md) |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| Grid size | 16×32 (half dense width, 2× throughput) |
| Effective MACs/cycle | 1,024 (dense equivalent) |
| Clock | 250 MHz |
| Area | ~2 mm² |
| Metadata storage | 2 bits / 4 weights in weight buffer |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| GB.1 | Golden sparse matmul | 2:4 sparse = dense bit-identical |
| GB.2 | Golden pruning algorithm | Correct 2-of-4 constraint |
| GB.3 | pymodel sparse grid | 2× throughput verified |
| GB.4 | RTL sparse decode | Activation mux correct |
| GB.5 | RTL sparse MAC array | Output vs golden |
| GB.6 | RTL fallback mode | Dense mode = PtahCore result |
| GB.7 | Synthesis | Gate count ≤ 4.5M |
| GB.8 | P&R | DRC-clean GDSII |

---

*Prev: [ImentetCore](03_ImentetCore_Attention.md) · Next: [BastCore — BF16 Tensor Core](05_BastCore_BF16Tensor.md)*
