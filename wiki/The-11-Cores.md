# 🗂️ The 11 Cores

A quick-reference overview of all KemetCore building blocks.

---

## Master Comparison Matrix

| Metric | SethCore | PtahConv | ImentetCore | GebCore | BastCore | AnubisCore | NeithCore | SobekCore | HapiCore | AtumCore |
|--------|:--------:|:--------:|:-----------:|:-------:|:--------:|:----------:|:---------:|:---------:|:--------:|:--------:|
| **RTL Modules** | ~25 | ~12 | ~10 | ~8 | ~10 | ~6 | ~15 | ~8 | ~8 | ~20+ |
| **Tests (estimate)** | ~80 | ~40 | ~35 | ~30 | ~35 | ~25 | ~50 | ~35 | ~60 | ~100+ |
| **Fmax Target** | 500 MHz | 250 MHz | 250 MHz | 250 MHz | 250 MHz | 1 GHz | 200 MHz | 500 MHz | 500 MHz | 500 MHz |
| **Gate Count** | ~50K | ~6M | ~3M | ~4M | ~4M | ~15K | ~100K | ~30K | ~30K | ~100K+ |
| **GDSII Area** | ~0.1 mm² | ~3 mm² | ~1.5 mm² | ~2 mm² | ~2 mm² | ~0.05 mm² | ~0.3 mm² | ~0.08 mm² | ~0.1 mm² | ~0.5 mm² |

---

## Core Details

### ⭐ RaCore — AI SoC (Capstone)
- **Deity:** Ra (supreme creator god)
- **Complexity:** ★★★★★
- **What it is:** The capstone project. Integrates all 10 cores plus the completed PtahCore into a single heterogeneous AI SoC over a shared NoC interconnect with a post-quantum root of trust.
- **KAI:** Kemet Accelerator Interface — one register + DMA contract for all cores
- **Tiers:** Lite (~3.5 mm², laptop-feasible) and Full (~16 mm², real shuttle target)
- **Status:** Phase 0/1 ✅ | RTL 🔧 (KAI regs, NoC arbiter, DMA engine shipping)

### ⭐ SethCore — RV32IM CPU
- **Deity:** Seth (god of chaos/strength)
- **Complexity:** ★★★★☆
- **What it is:** 5-stage in-order pipelined RISC-V RV32IM CPU. Classic Harvard microarchitecture with full data forwarding, 2-bit branch predictor + BTB, pipelined multiply (4-cycle), non-restoring divide. Verified bit-exact against Spike.
- **Features:** 5-stage pipeline (F/D/E/M/W), full forwarding network, 2 KiB I-cache + D-cache, AXI4 memory interface
- **Status:** Phase 0/1 ✅ | RTL 🔧 | Synthesis 🔧

### ⭐ PtahConv — Convolution Accelerator
- **Deity:** Ptah (god of craftsmen)
- **Complexity:** ★★★☆☆
- **What it is:** Direct 2D convolution accelerator — a systolic PE array that convolves without im2col. Supports standard 2D, depthwise, pointwise (1×1), and dilated convolutions. FP8-native using PtahCore's pipeline.
- **Features:** Weight-stationary/Output-stationary dual dataflow, built-in ReLU/ReLU6/GELU, padding on-the-fly, 32×16 PE array
- **Status:** Phase 0/1 ✅ | RTL 🔧 (conv2d engine shipped)

### ⭐ ImentetCore — Attention Unit
- **Deity:** Imentet (goddess of welcome/western afterlife)
- **Complexity:** ★★★☆☆
- **What it is:** Dedicated fused multi-head attention accelerator for transformer inference. Computes QK^T → online softmax → PV in one pass through a pipelined datapath.
- **Features:** Online softmax (single-pass), LUT-based exp + Newton reciprocal, FP8 accumulate, causal mask support, grouped-query attention (GQA)
- **Status:** Phase 0/1 ✅ | RTL ⬜

### ⭐ GebCore — Sparse Matmul
- **Deity:** Geb (god of the earth)
- **Complexity:** ★★★☆☆
- **What it is:** 2:4 structured sparse matmul accelerator (same sparse compute primitive as NVIDIA Ampere/Hopper). Every 4-weight group contains exactly 2 non-zeros.
- **Features:** Dense-sparse hybrid (both operands can be sparse), FP8 native, online pruning, transparent dense fallback, 16×32 sparse grid, 44% weight compression
- **Status:** Phase 0/1 ✅ | RTL 🔧 | Synthesis 🔧

### ⭐ BastCore — BF16 Tensor Core
- **Deity:** Bastet (goddess of protection/cats)
- **Complexity:** ★★☆☆☆
- **What it is:** BF16 tensor core — PtahCore adapted for bfloat16 (the LLM standard). Same architecture, wider datapaths. No subnormal complexity.
- **Features:** 16×16 MAC grid, BF16 decode/encode, FP32 accumulate, interface-compatible with PtahCore
- **Status:** Phase 0/1 ✅ | RTL 🔧 | Synthesis 🔧

### ⭐ AnubisCore — Hash Engine
- **Deity:** Anubis (god of embalming, fitting for "digesting" data)
- **Complexity:** ★★☆☆☆
- **What it is:** Cryptographic hash accelerator supporting SHA-256, SHA-224, SHA-384, SHA-512, SHA3-256, SHA3-384, and SHA3-512.
- **Features:** Unified frontend with mode selection, automatic message padding, 1 GHz target, ~15K gates
- **Status:** Phase 0/1 ✅ | RTL ✅ | Synthesis 🔧

### ⭐ NeithCore — ML-KEM (Kyber)
- **Deity:** Neith (goddess of war/wisdom/weaving)
- **Complexity:** ★★★★☆
- **What it is:** NIST-standardized post-quantum key encapsulation mechanism (FIPS 203) in hardware. Implements KeyGen, Encaps, and Decaps with optimized NTT engine.
- **Features:** Barrett/Montgomery reduction, pipelined radix-2 butterfly, CBD + PRF sampler, polynomial multiply, coefficient compression
- **Status:** Phase 0/1 ✅ | RTL 🔧 (polyaddsub, pointwise, polymul, msgcodec, CBD shipping) | Synthesis 🔧

### ⭐ SobekCore — Ray Tracer
- **Deity:** Sobek (god of the Nile/crocodiles)
- **Complexity:** ★★★☆☆
- **What it is:** Hardware ray-triangle intersection unit. Möller-Trumbore algorithm in a fully pipelined 5-stage datapath. 1 ray vs 1 triangle per cycle.
- **Features:** Watertight edge handling, FP32 precision, 5-stage pipeline (SUB→CROSS→DOT→RECIP→MULT), backface culling
- **Status:** Phase 0/1 ✅ | RTL ⬜

### ⭐ HapiCore — FPU Library
- **Deity:** Hapi (god of the Nile flood)
- **Complexity:** ★★☆☆☆
- **What it is:** Parameterized IEEE-754 floating-point unit library. Every other project depends on it for FP arithmetic.
- **Formats:** FP16, BF16, FP32, FP64. Operations: ADD, SUB, MUL, FMA, DIV, SQRT, CMP, CVT. Rounding modes: RNE, RTZ, RDN, RUP, RMM.
- **Status:** Phase 0/1 ✅ | RTL 🔧 (fp32 minmax, compare, classify, int↔fp32 convert shipping) | Synthesis 🔧

### ⭐ AtumCore — RISC-V Vector
- **Deity:** Atum (the creator god)
- **Complexity:** ★★★★★
- **What it is:** Full RISC-V Vector Extension v1.0 coprocessor. Decoupled execution with 32 × VLEN vector register file, 8 mask registers, 8 ALU lanes, and vector LSU.
- **Features:** VLEN=256, ELEN=64, strip-mining, all RVV v1.0 instruction groups (config, load/store, strided, indexed, integer, multiply, compare, FP, permute, reduction)
- **Status:** Phase 0/1 ✅ | RTL 🔧 (vadd, vsub, vmul, vdiv, vfsqrt, vfredsum, vcompress, vrgather, vslide, vmvsx, vredminmax shipping)
