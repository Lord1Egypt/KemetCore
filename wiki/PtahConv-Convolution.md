# 🧠 PtahConv — Direct Convolution Accelerator

> **Deity:** Ptah (𓁰, god of craftsmen and architecture)
> **Complexity:** ★★★☆☆
> **Gates:** ~6M | **Fmax:** 250 MHz | **Area:** ~3 mm²

---

## Overview

A **direct convolution accelerator** — 2D systolic PE array that computes convolutions without im2col. Extends the PtahCore ecosystem: PtahCore handles fully-connected (matmul), PtahConv handles convolutional layers.

---

## Core Innovation

Instead of im2col (which expands memory 9-27× for 3×3 conv), the PE array holds filter weights while input feature maps stream through. Each PE accumulates partial sums and passes eastward.

| Feature | PtahConv | Im2col+Matmul |
|---------|:--------:|:-------------:|
| Memory expansion | 1× (in-place) | 9-27× |
| Dataflow | Dual (WS + OS) | Fixed |
| Fused activation | In-hardware ReLU/GELU | Additional pass |
| FP8-native | ✅ | INT8 only |

---

## Supported Convolutions

| Type | Supported |
|------|:---------:|
| Standard 2D conv | ✅ |
| Depthwise conv (groups=C_in) | ✅ |
| Pointwise 1×1 | ✅ |
| Dilated conv | ✅ |
| Transposed conv | ❌ (future) |

---

## RTL Status

Recently shipped: `ptah_conv2d` — the direct 2D convolution engine. Module hierarchy includes PE array, grid, sequencer, IFM stream, filter loader, and activation units.
