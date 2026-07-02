# 🧠 BastCore — BF16 Tensor Core

> **Deity:** Bastet (goddess of protection, cats, and the home)
> **Complexity:** ★★☆☆☆
> **Gates:** ~4M | **Fmax:** 250 MHz | **Area:** ~2 mm²

---

## Overview

PtahCore's architecture adapted for **bfloat16** — the format that powers every modern LLM. Same systolic array, wider datapath. FP32 accumulate, 16×16 grid.

---

## Why BF16?

| Format | Exponent | Range | Where Used |
|--------|:--------:|:-----:|------------|
| FP8 e4m3 | 4 | ±240 | Inference |
| FP16 | 5 | ±65504 | Mixed precision |
| **BF16** | **8** | **±3.4e38** | **LLM training + inference** |
| FP32 | 8 | ±3.4e38 | Accumulation |

BF16 has the same dynamic range as FP32 (8-bit exponent) with enough precision for training. It's the standard for transformers.

---

## Key Simplification vs PtahCore

BF16 is literally the upper 16 bits of FP32 — encoding is a truncation, decoding is zero-padding. No subnormal handling needed. Same pipeline depth (2 stages), smaller grid (16×16 vs 32×32).

---

## Interface Compatibility

Interface-compatible with PtahCore — same SMEM, barrier, cmdproc, and load/store interfaces. Wider datapaths but identical protocol.
