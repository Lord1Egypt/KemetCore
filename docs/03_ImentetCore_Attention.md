# 𓁼 ImentetCore — Transformer Attention Unit

> **Deity:** Imentet (𓁼, goddess of welcome and the western afterlife)
> **Domain:** ML — Transformer Attention
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 250 MHz on ASAP7
> **Est. Gates:** ~3M
> **Complexity:** ★★★☆☆

---

## 1. Technical Overview

ImentetCore is a **dedicated fused multi-head attention (MHA) accelerator** for transformer inference. It computes the full attention function in hardware:

```
Attention(Q, K, V) = softmax(Q × K^T / sqrt(d_k)) × V
```

Rather than routing QKV projections to a general-purpose matmul array, ImentetCore uses dedicated datapaths for each attention sub-operation: score matmul, softmax, and weighted sum. This allows extreme pipelining — all tokens in a sequence are processed concurrently through the attention pipeline.

### Key Innovations

| Feature | ImentetCore | Software Attention |
|---------|-------------|-------------------|
| **Fused pipeline** | QK→softmax→PV in one pass | Three separate kernel launches |
| **Hardware softmax** | LUT-based exp + Newton reciprocal | exp/div in software (costly) |
| **Online softmax** | Single-pass (no two-pass reduction) | Two-pass |
| **FP8 accumulate** | Shared PtahCore FP8 pipeline | Usually FP16/FP32 |

---

## 2. Architecture

### Core Dataflow

```
Q_buffer ──┐
            ├──▶ matmul (QK^T) ──▶ online softmax ──▶ matmul (PV) ──▶ output
K_buffer ──┘         ▲                              ▲
                     │                              │
                 score_buf                       V_buffer
```

The array is divided into three sections:
1. **QK Matmul** — 32×32 systolic array (same as PtahCore)
2. **Online Softmax** — 32-PE row with FSM for single-pass softmax
3. **PV Matmul** — 32×32 systolic array

### Module Hierarchy

```
imentetcore/
├── imentet_top.sv             # Top-level + control FSM
├── imentet_qk_matmul.sv       # Q × K^T systolic array (32×32)
├── imentet_score_buf.sv       # Score buffer (SRAM, 32×32)
├── imentet_online_softmax.sv  # Online softmax engine (32 PEs)
├── imentet_pv_matmul.sv       # softmax(QK) × V systolic array
├── imentet_output_buf.sv      # Output buffer
├── imentet_controller.sv      # Layer execution FSM
├── imentet_exp.sv             # Exponential function unit (LUT + poly)
├── imentet_reciprocal.sv      # Newton-Raphson reciprocal unit
└── imentet_causal_mask.sv     # Causal mask logic (for decoder)
```

### Attention Variants Supported

| Variant | Support | Notes |
|---------|:-------:|-------|
| Multi-head attention | ✅ | Standard MHA |
| Causal (decoder) | ✅ | Triangular mask |
| Cross-attention | ✅ | KV from encoder |
| Grouped-query (GQA) | ✅ | N_heads > K_V_heads |
| Multi-query (MQA) | ❌ | Future |

### Softmax Pipeline

```
score[i] ──▶ exp(score[i] - max_score) ──▶ accumulate sum ──▶ divide
```

Online softmax eliminates the two-pass requirement:

1. Track `m = max(score)` and `d = sum(exp(score - m))` in one pass
2. Output `exp(score - m) / d` per element

---

## 3. Golden Reference

```
golden/
├── attention.py               # NumPy multi-head attention
├── online_softmax.py          # Online (single-pass) softmax
├── causal_mask.py             # Triangular mask generation
├── gqa.py                     # Grouped-query attention
└── tests/
    ├── test_attention.py      # Random vs PyTorch
    ├── test_softmax.py        # Numerical accuracy (LUT vs full)
    ├── test_causal.py         # Causal mask correctness
    └── test_gqa.py            # GQA parity with standard MHA
```

---

## 4. Testing Strategy

| Test Layer | Count | What It Verifies |
|------------|:-----:|------------------|
| Golden: random vs torch | 8 | Various seq_len, d_model, n_heads |
| Golden: numerical | 4 | Softmax error bound ≤ ULP |
| pymodel: softmax FSM | 4 | Single-pass vs two-pass |
| pymodel: full pipeline | 4 | End-to-end attention |
| RTL: exp unit | 4 | LUT accuracy + out-of-range |
| RTL: reciprocal | 3 | Newton convergence |
| RTL: softmax pipeline | 4 | Full softmax in one pass |
| RTL: full chip | 4 | Attention output vs golden |
| **Total** | **~35** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| PtahCore | FP8 encode/decode, MAC array | [Lord1Egypt/PtahCore](https://github.com/Lord1Egypt/PtahCore) |
| PtahConv | Activation unit (optional) | [docs/02_PtahConv_Convolution.md](02_PtahConv_Convolution.md) |
| HapiCore | FP32 add (for softmax accumulator) | [docs/09_HapiCore_FPU.md](09_HapiCore_FPU.md) |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| QK array | 32×32 (same as PtahCore) |
| PV array | 32×32 |
| Softmax PEs | 32 |
| Clock | 250 MHz |
| Area | ~1.5 mm² |
| Score buffer | 4 KiB |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| IM.1 | Golden attention reference | Bit-exact vs PyTorch |
| IM.2 | Online softmax golden | Single-pass correctness |
| IM.3 | pymodel full pipeline | Cycle-level attention |
| IM.4 | RTL exp + reciprocal units | IEEE-754 compliant |
| IM.5 | RTL softmax datapath | Single-pass pipeline |
| IM.6 | RTL full chip | Attention output vs golden |
| IM.7 | Synthesis | Gate count ≤ 3.5M |
| IM.8 | P&R | DRC-clean GDSII |

---

*Prev: [PtahConv](02_PtahConv_Convolution.md) · Next: [GebCore — Sparse Matmul](04_GebCore_SparseMatmul.md)*
