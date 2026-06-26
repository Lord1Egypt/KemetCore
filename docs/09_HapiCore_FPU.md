# 𓎛 HapiCore — IEEE-754 Floating-Point Unit Generator

> **Deity:** Hapi (𓎛, god of the Nile flood — the source of fertility that "flows" through all other projects)
> **Domain:** Computer Arithmetic
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 500 MHz on ASAP7
> **Est. Gates:** ~30K (all formats combined)
> **Complexity:** ★★☆☆☆

---

## 1. Technical Overview

HapiCore is a **parametrized floating-point unit (FPU) library** — a set of SystemVerilog modules that implement IEEE-754 arithmetic operations for multiple floating-point formats. It is the **foundation project** for KemetCore: every other project depends on it for correct FP arithmetic.

### Supported Formats

| Format | Total Bits | Exponent | Mantissa | Bias | Used By |
|--------|:----------:|:--------:|:--------:|:----:|---------|
| FP16 (binary16) | 16 | 5 | 10 | 15 | ML, graphics |
| BF16 | 16 | 8 | 7 | 127 | ML training |
| FP32 (binary32) | 32 | 8 | 23 | 127 | All projects |
| FP64 (binary64) | 64 | 11 | 52 | 1023 | Scientific |
| TF32 (NVIDIA) | 19 | 8 | 10 | 127 | ML (future) |

### Supported Operations

| Operation | FP16 | BF16 | FP32 | FP64 | Cycles (FP32) |
|-----------|:----:|:----:|:----:|:----:|:-------------:|
| ADD | ✅ | ✅ | ✅ | ✅ | 1 (pipelined) |
| SUB | ✅ | ✅ | ✅ | ✅ | 1 |
| MUL | ✅ | ✅ | ✅ | ✅ | 1 |
| FMA | ✅ | ✅ | ✅ | ✅ | 2 |
| DIV | ✅ | ✅ | ✅ | ✅ | 12 (Goldschmidt) |
| SQRT | ❌ | ❌ | ✅ | ✅ | 14 (Newton) |
| CMP | ✅ | ✅ | ✅ | ✅ | 1 |
| CVT | ✅ | ✅ | ✅ | ✅ | 1–2 |

---

## 2. Architecture

### Parameterized Module Design

Each module uses SystemVerilog parameters to select the format:

```systemverilog
module fp_add #(
    parameter int EW = 8,   // Exponent width
    parameter int MW = 23   // Mantissa width
)(
    input  logic [EW+MW:0] a, b,  // FP numbers
    input  logic          rmode,  // Rounding mode (0=RNE, 1=RTZ)
    output logic [EW+MW:0] result
);
```

This allows a single `fp_add.sv` to be instantiated for FP16, BF16, FP32, or FP64 by setting parameters.

### Module Hierarchy

```
hapicore/
├── fp_add.sv                  # Addition/subtraction (all formats)
├── fp_mul.sv                  # Multiplication (all formats)
├── fp_fma.sv                  # Fused multiply-add
├── fp_div.sv                  # Division (Goldschmidt algorithm)
├── fp_sqrt.sv                 # Square root (Newton-Raphson)
├── fp_cmp.sv                  # Comparison (with NaN handling)
├── fp_cvt.sv                  # Format conversion
├── fp_round.sv                # Rounding (RNE, RTZ, RDN, RUP, RMM)
├── fp_exception.sv            # Exception flags (NV, OF, UF, NX, DZ)
└── fp_classify.sv             # NaN, Inf, zero, subnormal detection
```

### FP32 Adder Datapath

```
a ───▶ unpack ──▶ align ──▶ add/sub ──▶ normalize ──▶ round ──▶ pack ──▶ result
b ───▶ unpack ──▶          ▲                              │
                   │                                       │
               exponent                                rounding
               difference                                increment
                 │                                       │
                 └── alignment shift ──────── extra bits ──┘
```

### FP32 Multiplier Datapath

```
a ───▶ unpack ──▶ mantissa mul (24×24) ──▶ normalize ──▶ round ──▶ pack ──▶ result
b ───▶ unpack ──▶                          ▲            │
                 │                    leading-zero      rounding
             exponent add             count (LZC)     increment
                 │                       │               │
                 └─── bias subtract ──────┘───────────────┘
```

### Goldschmidt Division

Used for FP32 and FP64 division. Converges quadratically:

```
Step 1:  x = 1 / b  (initial estimate, LUT)
Step 2:  repeat:
           f = 2 − b × x
           x = x × f
           q = q × f
         (3 iterations for FP32, 4 for FP64 → 12–16 cycles)
```

---

## 3. Golden Reference

```
golden/
├── fp_add.py                  # Bit-exact float add (all formats)
├── fp_mul.py                  # Bit-exact float multiply
├── fp_fma.py                  # Bit-exact FMA
├── fp_div.py                  # Bit-exact division
├── fp_sqrt.py                 # Bit-exact square root
├── fp_round.py                # Rounding modes
├── fp_special.py              # NaN, Inf, zero, subnormal handling
└── tests/
    ├── test_add.py            # Exhaustive FP16 + random FP32/FP64
    ├── test_mul.py            # Same
    ├── test_fma.py            # FMA vs separate add+compare
    ├── test_div.py            # Division correctness
    ├── test_round.py          # All rounding modes
    ├── test_special.py        # NaN propagation, inf handling
    └── test_exhaustive.py     # FP16: all 2^16 combinations
```

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: FP16 exhaustive | 4 | ADD, MUL, FMA, DIV: all 2^16×2^16 (sampled) |
| Golden: FP32 random | 2 | 10K random pairs |
| Golden: special values | 6 | NaN, Inf, zero, subnormals |
| Golden: rounding | 4 | All 5 IEEE modes verified |
| pymodel: pipeline | 4 | Cycle-level correctness |
| RTL: FP16 add | 4 | Exhaustive small + random |
| RTL: FP32 mul | 4 | Random + edge + special |
| RTL: FP32 div | 4 | Random + edge |
| RTL: all formats | 6 | Cross-format conversions |
| **Total** | **~38** | |

### IEEE-754 Compliance Tests

Every operation is tested against the IEEE-754-2019 standard:

| Requirement | Test |
|-------------|------|
| Correct rounding | All 5 rounding modes produce correct least-significant bit |
| NaN propagation | Quiet NaN → quiet, signaling NaN → quiet + exception |
| Inf arithmetic | Inf ± Inf, Inf × 0, 0/0 → NaN; valid operations → correct |
| Signed zero | −0 and +0 behave correctly in all operations |
| Subnormals | Gradual underflow when enabled, flush-to-zero when disabled |
| Exception flags | NV (invalid), OF (overflow), UF (underflow), NX (inexact), DZ (divide-by-zero) |

---

## 5. Dependencies

| Dependency | Why |
|------------|-----|
| None | HapiCore is the foundation — no other hardware deps |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| Clock | 500 MHz (all formats) |
| FP16/BF16 area | ~2K gates each |
| FP32 area | ~8K gates (add + mul + FMA) |
| FP64 area | ~15K gates (add + mul + div) |
| Total area | ~0.1 mm² |
| Pipeline depth | 2 stages (add, mul), 4 stages (div) |

---

## 7. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| HA.1 | Golden: FP16 add/mul | Exhaustive 2^16 × 2^16 (sampled) |
| HA.2 | Golden: FP32 all ops | 10K random each |
| HA.3 | Golden: IEEE-754 specials | NaN/Inf/zero/subnormal |
| HA.4 | Golden: rounding | All 5 IEEE modes |
| HA.5 | pymodel: fp_add | 2-stage pipeline |
| HA.6 | pymodel: fp_mul | 2-stage pipeline |
| HA.7 | pymodel: fp_fma | 2-stage pipeline |
| HA.8 | RTL: fp_add (param) | IEEE-754 pass |
| HA.9 | RTL: fp_mul (param) | IEEE-754 pass |
| HA.10 | RTL: fp_fma (param) | IEEE-754 pass |
| HA.11 | RTL: fp_div (FP32) | Goldschmidt 12 cycles |
| HA.12 | RTL: fp_sqrt (FP32) | Newton 14 cycles |
| HA.13 | Synthesis: all formats | Gate count ≤ expectations |
| HA.14 | P&R: FP32 add/mul/FMA | DRC clean, timing closed |

---

## 8. Interface

```systemverilog
// FP32 addition example
logic [31:0] a, b, result;
logic [4:0]  exception;  // {NV, OF, UF, NX, DZ}

fp_add #(.EW(8), .MW(23)) u_fp_add (
    .a(a),
    .b(b),
    .rmode(2'b00),       // RNE
    .result(result),
    .exception(exception)
);
```

---

*Prev: [SobekCore](08_SobekCore_RayTrace.md) · Next: [AtumCore — RVV](10_AtumCore_RVV.md)*
