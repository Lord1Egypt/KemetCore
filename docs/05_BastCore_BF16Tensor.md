# 𓎯 BastCore — BF16 Tensor Core

> **Deity:** Bastet (𓎯, goddess of protection, cats, and the home)
> **Domain:** ML — BF16 Matrix Multiplication
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 250 MHz on ASAP7
> **Est. Gates:** ~4M
> **Complexity:** ★★☆☆☆

---

## 1. Technical Overview

BastCore is a **bfloat16 tensor core** — essentially PtahCore's architecture adapted for BF16 compute. While PtahCore uses FP8 (e4m3 + e5m2), BastCore uses the bfloat16 format that has become the standard for LLM training and inference.

### Why BF16?

| Format | Exponent | Mantissa | Range | Precision | Where Used |
|--------|:--------:|:--------:|:-----:|:---------:|------------|
| FP8 e4m3 | 4 | 3 | ±240 | Low | Inference |
| FP8 e5m2 | 5 | 2 | ±57344 | Lower | Inference (gradients) |
| **BF16** | **8** | **7** | **±3.4e38** | **Medium** | **Training & inference** |
| FP16 | 5 | 10 | ±65504 | High | Mixed precision |
| FP32 | 8 | 23 | ±3.4e38 | Full | Accumulation |

### Key Simplification vs PtahCore

- **No subnormal handling needed** — BF16 subnormals are rare (range is large)
- **Same pipeline depth** — 2-stage (decode→mul→accumulate)
- **Smaller grid** — 16×16 instead of 32×32 (area is ~2× per cell)
- **Same tooling** — reuse PtahCore's pymodel, testbench, and P&R scripts

---

## 2. Architecture

BastCore reuses the **exact same architecture** as PtahCore but with wider datapaths:

| Component | PtahCore (FP8) | BastCore (BF16) |
|-----------|:--------------:|:----------------:|
| Input format | FP8 (8-bit) | BF16 (16-bit) |
| Encode (FP32→format) | fp8_encode.sv | bf16_encode.sv |
| Decode (format→FP32) | fp8_decode.sv | bf16_decode.sv |
| Multiply | fp32_mul.sv | Same (FP32 is native) |
| Add/accumulate | fp32_add.sv | Same |
| MAC grid | 32×32 | 16×16 |
| TMEM width | 4×FP32 per cell | Same |
| Grid throughput | 1,024 MAC/cycle | 256 MAC/cycle |

### Module Modifications

```
bastcore/
├── bf16_decode.sv             # BF16 → FP32 (was fp8_decode.sv)
├── bf16_encode.sv             # FP32 → BF16 (was fp8_encode.sv, simpler)
├── mac_cell_bf16.sv           # 2-stage MAC with wider decode
├── mac_grid_bf16.sv           # 16×16 abutted grid
├── mma_unit_bf16.sv           # Operand-fetch FSM (wider smem_read)
└── ...rest from PtahCore...
```

### Interface Compatibility

BastCore is designed to be interface-compatible with PtahCore:

- Same `smem` interface (wider read: 32-bit instead of 16-bit per cell)
- Same `barrier` interface (no changes needed)
- Same `cmdproc` interface (instructions are the same)
- Same `load`/`store` engines (wider datapath but same protocol)

---

## 3. Golden Reference

```
golden/
├── bf16.py                    # BF16 encode/decode (numpy float32→uint16)
├── matmul_reference_bf16.py   # BF16 matmul (numpy adaptation)
└── tests/
    ├── test_bf16.py           # Roundtrip: FP32→BF16→FP32
    ├── test_bf16_matmul.py    # Random vs numpy float64
    └── test_bf16_accuracy.py  # Error bound analysis
```

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: BF16 encode/decode | 6 | Roundtrip, boundaries, saturation |
| Golden: matmul | 6 | Random vs numpy |
| pymodel: full array | 6 | 16×16 cycle-level mac |
| pymodel: end-to-end | 4 | Full kernel execution |
| RTL: bf16_decode | 4 | Exhaustive for small range + random |
| RTL: bf16_encode | 4 | Same |
| RTL: mac cell | 6 | 16-step chain |
| RTL: full chip | 6 | E2E vs golden |
| **Total** | **~42** | |

---

## 5. Special Considerations

### BF16 Encode is Simpler than FP8

BF16 is literally the upper 16 bits of FP32. Encoding is a truncation:
```python
def fp32_to_bf16(f):
    bits = struct.pack('>f', f)
    sixteen_bits = bits[:2]  # Take top 16 bits
    # That's it. (Rounding optional)
```

### BF16 Decode is Freeze/Zero-Pad

```python
def bf16_to_fp32(b):
    bits = b + b'\x00\x00'  # Pad with 16 zero LSBs
    return struct.unpack('>f', bits)[0]
```

This means the decode logic is **zero hardware** — literally connecting wires with zero-padding. This makes BastCore's decode area negligible vs PtahCore's combinational decode tree.

---

## 6. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| HapiCore | FP32 mul/add (shared or customized) | [docs/09_HapiCore_FPU.md](09_HapiCore_FPU.md) |
| PtahCore | Architecture template, P&R scripts | [Lord1Egypt/PtahCore](https://github.com/Lord1Egypt/PtahCore) |

---

## 7. Physical Design

| Parameter | Target |
|-----------|--------|
| Grid size | 16×16 |
| MACs/cycle | 256 |
| Clock | 250 MHz |
| Cell area | ~2× PtahCore's (wider mux, same add/mul) |
| Grid area | ~2 mm² |
| TMEM | 4×FP32×256 = 4,096 FP32 values |

---

## 8. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| BA.1 | BF16 golden model | encode/decode + matmul |
| BA.2 | pymodel adapted from PtahCore | 16×16 array |
| BA.3 | bf16_encode/decode RTL | Simplify (wire + truncate) |
| BA.4 | mac_cell_bf16 | 2-stage pipelined |
| BA.5 | Full grid RTL | 16×16 abutted |
| BA.6 | Synthesis | Gate count, 0 latches |
| BA.7 | P&R | DRC-clean GDSII |

---

*Prev: [GebCore](04_GebCore_SparseMatmul.md) · Next: [AnubisCore — Hash Engine](06_AnubisCore_HashEngine.md)*
