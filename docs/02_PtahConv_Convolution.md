# 𓁰 PtahConv — Direct Convolution Accelerator

> **Deity:** Ptah (𓁰, god of craftsmen and architecture — also PtahCore's namesake)
> **Domain:** ML — Convolution Neural Networks
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 250 MHz on ASAP7 (matching PtahCore clock domain)
> **Est. Gates:** ~6M (32×16 PE array)
> **Complexity:** ★★★☆☆

---

## 1. Technical Overview

PtahConv is a **direct convolution accelerator** — a 2D systolic PE array that computes convolutions without im2col. It extends the PtahCore ecosystem by adding CNN support. While PtahCore handles fully-connected layers (matrix multiplies), PtahConv handles convolutional layers directly.

### The Core Idea

Instead of im2col (which expands memory by a factor of 9–27× for 3×3 conv), PtahConv streams the input feature map through the array, with each PE holding a single filter weight. The PEs compute partial sums locally and pass them eastward, accumulating across the spatial dimensions.

### Key Innovations

| Innovation | PtahConv | Prior Art (Systolic Conv) |
|------------|----------|---------------------------|
| **Dual dataflow** | Weight-stationary for dense, output-stationary for depthwise | Usually one or the other |
| **FP8-native** | Uses PtahCore's FP8 encode/decode pipeline | Usually INT8 |
| **Fused activation** | Built-in ReLU, ReLU6, GELU post-MAC | Usually external |
| **Padding on-the-fly** | Zero-pad logic in the input stream | Usually requires pre-padded buffer |

---

## 2. Architecture

### PE Array

```
IFM Stream (west→east)
     │
     ▼
┌────┬────┬────┬────┐
│ W00 │ W01 │ W02 │ W03 │  K_h │
├────┼────┼────┼────┤      │
│ W10 │ W11 │ W12 │ W13 │      K_w
├────┼────┼────┼────┤      │
│ W20 │ W21 │ W22 │ W23 │      ▼
├────┼────┼────┼────┤     K_h × K_w PEs per row
│ W30 │ W31 │ W32 │ W33 │
└────┴────┴────┴────┘
     │
     ▼
  Partial sums (east→drain strip)
```

Each PE in the array contains:
- **FP8 decode** → FP32 weight (stored permanently during layer execution)
- **FP8 decode** → FP32 input element (streamed column-by-column)
- **FP32 multiply** → partial product
- **FP32 accumulator** (from PtahCore's mac_cell)
- **Row feedthrough** for vertical IFM passing

### Module Hierarchy

```
ptahconv/
├── ptahconv_top.sv            # Top-level controller
├── ptahconv_pe.sv             # Processing element (weight + MAC)
├── ptahconv_row.sv            # Row of PEs (horizontal pass)
├── ptahconv_grid.sv           # 2D PE grid (K_h × K_w)
├── ptahconv_sequencer.sv      # Conv loop sequencer (OHWC→calculator)
├── ptahconv_ifm_stream.sv     # IFM streaming engine (from SMEM)
├── ptahconv_filter_load.sv    # Filter weight loader (from SMEM)
├── ptahconv_activation.sv     # Post-MAC activation (ReLU/GELU)
├── ptahconv_pool.sv           # Optional pooling (avg/max)
├── ptahconv_drain.sv          # OFM drain to SMEM/TMEM
└── ptahconv_controller.sv     # Layer execution FSM
```

### Supported Convolution Types

| Type | Support | Notes |
|------|:-------:|-------|
| Standard 2D conv | ✅ | Same as torch.nn.Conv2d |
| Depthwise conv | ✅ | groups = in_channels |
| Pointwise conv (1×1) | ✅ | Degenerates to matmul |
| Dilated conv | ✅ | configurable dilation |
| Transposed conv | ❌ Phase 2 | Future extension |
| Grouped conv | ❌ | Complex dataflow; future |

---

## 3. Golden Reference

```
golden/
├── convolution.py             # Direct convolution reference
├── im2col_conv.py             # im2col + matmul (for comparison)
├── activations.py             # ReLU, ReLU6, GELU, SiLU
├── padding.py                 # Zero, reflect, replicate padding
├── conv_problem.py            # Problem definition dataclass
└── tests/
    ├── test_conv_vs_torch.py  # Random tensors vs PyTorch
    ├── test_activations.py    # Bit-exact comparison
    ├── test_padding.py        # Padding correctness
    └── test_edge_cases.py     # 1×1, stride>1, depthwise
```

---

## 4. Testing Strategy

| Test Layer | Count | What It Verifies |
|------------|:-----:|------------------|
| Golden: random vs torch | 10 | Random IFM/filter shapes, various params |
| Golden: edge cases | 5 | 1×1, depthwise, stride>1, dilation |
| pymodel: sequencer | 5 | Loop ordering, boundary conditions |
| pymodel: PE array | 8 | Single PE, row, grid, drain |
| pymodel: end-to-end | 4 | Full convolution layer |
| RTL: PE | 6 | Decode→MAC→accumulate→drain |
| RTL: grid | 6 | Feedthrough, partial sum, final output |
| RTL: integration | 4 | Full conv with activation+pooling |
| **Total** | **~48** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| PtahCore | FP8 encode/decode, MAC pipeline | [Lord1Egypt/PtahCore](https://github.com/Lord1Egypt/PtahCore) |
| BastCore | BF16 datapath (for FP16 support) | [docs/05_BastCore_BF16Tensor.md](05_BastCore_BF16Tensor.md) |
| HapiCore | FP32 add/mul (shared FPU) | [docs/09_HapiCore_FPU.md](09_HapiCore_FPU.md) |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| PE array | 32×16 (K_h × K_w max) |
| MAC width | FP8→FP32 (from PtahCore) |
| Clock | 250 MHz (synchronous with PtahCore) |
| Grid area | ~3 mm² (estimated) |
| IFM buffer | 16 KiB (on-chip SRAM) |
| Filter buffer | 8 KiB (on-chip SRAM) |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| PC.1 | Golden convolution reference | Bit-exact vs PyTorch |
| PC.2 | pymodel sequencer + PE array | Correct dataflow |
| PC.3 | RTL PE row | Single row driving pattern |
| PC.4 | RTL full grid | 2D convolution output |
| PC.5 | RTL + activation/pool | Full conv layer |
| PC.6 | Synthesis | Gate count ≤ 7M |
| PC.7 | P&R | DRC-clean GDSII |

---

*Prev: [SethCore](01_SethCore_RV32IM_CPU.md) · Next: [ImentetCore](03_ImentetCore_Attention.md)*
