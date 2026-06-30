# 📐 HapiCore — IEEE-754 FPU Library

> **Deity:** Hapi (god of the Nile flood — the source that "flows" through all other projects)
> **Complexity:** ★★☆☆☆
> **Gates:** ~30K | **Fmax:** 500 MHz | **Area:** ~0.1 mm²

---

## Overview

The **foundation project** for all of KemetCore. A parameterized SystemVerilog library of IEEE-754 floating-point units. Every other project depends on HapiCore for correct FP arithmetic — no exceptions.

---

## Supported Formats

| Format | Total Bits | E | M | Bias | Used By |
|--------|:----------:|:-:|:-:|:----:|---------|
| FP16 | 16 | 5 | 10 | 15 | ML, graphics |
| BF16 | 16 | 8 | 7 | 127 | ML training (LLMs) |
| FP32 | 32 | 8 | 23 | 127 | All projects |
| FP64 | 64 | 11 | 52 | 1023 | Scientific |

---

## Supported Operations

| Op | FP16 | BF16 | FP32 | FP64 | Cycles (FP32) |
|----|:----:|:----:|:----:|:----:|:-------------:|
| ADD/SUB | ✅ | ✅ | ✅ | ✅ | 1 |
| MUL | ✅ | ✅ | ✅ | ✅ | 1 |
| FMA | ✅ | ✅ | ✅ | ✅ | 2 |
| DIV | ✅ | ✅ | ✅ | ✅ | 12 (Goldschmidt) |
| SQRT | — | — | ✅ | ✅ | 14 (Newton) |
| CMP | ✅ | ✅ | ✅ | ✅ | 1 |
| CVT | ✅ | ✅ | ✅ | ✅ | 1–2 |

---

## Architecture

All modules are parameterized:
```systemverilog
module fp_add #(parameter EW = 8, MW = 23)  // EW=Exponent width, MW=Mantissa width
```

One `fp_add.sv` instantiates for FP16, BF16, FP32, or FP64 by changing two parameters.

---

## Current RTL Status

| Module | Status |
|--------|:------:|
| `hapi_fp32_cmp` | ✅ Compare with NaN handling |
| `hapi_fp32_minmax` | ✅ Min/max |
| `hapi_fp32_class` | ✅ Classify (NaN, Inf, zero, subnormal) |
| `hapi_int_to_fp32` | ✅ Integer to FP32 conversion |
| `hapi_fp32_to_int` | ✅ FP32 to integer conversion |

Remaining: fp_add, fp_mul, fp_fma, fp_div, fp_sqrt, fp_cvt (multi-format).

---

## Dependency Role

```
HapiCore → BastCore (BF16 multiply)
HapiCore → SethCore (FPU for M extension)
HapiCore → SobekCore (FP32 ray intersection)
HapiCore → AtumCore (all vector FP ops)
HapiCore → ImentetCore (softmax exp/div)
```
