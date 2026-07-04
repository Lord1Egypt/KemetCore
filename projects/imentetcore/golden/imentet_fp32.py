"""ImentetCore fp32 datapath primitives — the hardware-accurate building blocks
the attention unit is assembled from.

The math reference in `imentet_attention.py` runs in float64 (the ideal answer,
incl. exp/softmax). The *hardware* evaluates the score datapath in IEEE-754 single
precision with a fixed evaluation order, so these primitives define that fp32 order
exactly and are the bit-exact golden the RTL (imentet_qk_score.sv, …) is checked
against. Every step is a correctly-rounded fp32 op (numpy float32 == the HapiCore
hapi_fp32_mul / hapi_fp32_add primitives).

The softmax (exp/max/sum-normalise) is deliberately NOT modelled here: exp is not
a correctly-rounded primitive we can bit-match, so it stays in the float64 math
reference. The scaled dot-product *score* Q·Kᵀ/√d, however, is a pure mul/add
datapath and is fully bit-exact.
"""
import numpy as np

D = 8  # head sub-tile width the imentet_qk_score datapath processes per call


def f32(x):
    return np.float32(x)


def bits(x):
    """fp32 value -> 32-bit pattern."""
    return int(np.float32(x).view(np.uint32))


def frombits(u):
    """32-bit pattern -> fp32 value."""
    return np.uint32(u & 0xFFFFFFFF).view(np.float32)


def dot(q, k):
    """D-element fp32 dot product, evaluated left-to-right the way the MAC datapath
    does: p_i = q_i * k_i (fp32), then acc = (((p0 + p1) + p2) + … + p_{D-1}), each
    add fp32. Inputs are fp32 values; returns the fp32 result."""
    p = [f32(f32(q[i]) * f32(k[i])) for i in range(D)]
    acc = p[0]
    for i in range(1, D):
        acc = f32(f32(acc) + f32(p[i]))
    return f32(acc)


def score(q, k, s):
    """Scaled dot-product attention score for one (query, key) pair:
        raw   = dot(q, k)          (fp32 fixed-order MAC)
        score = raw * s            (fp32 multiply by the 1/√d scale)
    `q`, `k` elements and `s` are fp32 values; returns one fp32 scalar."""
    return f32(f32(dot(q, k)) * f32(s))


def score_bits(qb, kb, sb):
    """score over 32-bit input patterns (q, k vectors, scalar s) -> 32-bit result."""
    q = [frombits(u) for u in qb]
    k = [frombits(u) for u in kb]
    return bits(score(q, k, frombits(sb)))
