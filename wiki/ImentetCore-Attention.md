# 🧠 ImentetCore — Transformer Attention

> **Deity:** Imentet (goddess of welcome and the western afterlife)
> **Complexity:** ★★★☆☆
> **Gates:** ~3M | **Fmax:** 250 MHz | **Area:** ~1.5 mm²

---

## Overview

Dedicated **fused multi-head attention accelerator** for transformer inference. Computes the full attention pipeline in hardware:

```
Q × K^T → Online Softmax → Softmax × V
```

No three-kernel-launch overhead — all tokens flow through a single pipelined datapath.

---

## Key Features

| Feature | ImentetCore | Software Attention |
|---------|:-----------:|:------------------:|
| Fused pipeline | 1 pass | 3 separate kernel launches |
| Softmax | Hardware LUT + Newton | exp/div in software |
| Softmax passes | Single-pass (online) | Two-pass |
| FP8 accumulate | ✅ | Usually FP16/FP32 |

---

## Architecture

```
Q_buffer ──┐
            ├──▶ QK Matmul (32×32 systolic) ──▶ Online Softmax ──▶ PV Matmul ──▶ output
K_buffer ──┘
                                           ▲
                                      V_buffer
```

Three pipelined sections: QK matmul → 32-PE online softmax FSM → PV matmul. Causal mask supported for decoder-style attention.
