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


# ---- weighted value accumulation (the second half of attention) -------------- #
L = 4   # keys/values per av_context tile
DV = 4  # value/context width per av_context tile


def av_context(w, V):
    """Weighted sum of value vectors: context[k] = sum_j w[j] * V[j][k], the
    second half of attention (probabilities · values). Each output element is a
    fixed left-to-right fp32 MAC over the L keys:
        p_j    = w[j] * V[j][k]
        ctx[k] = (((p_0 + p_1) + …) + p_{L-1})
    `w` is L fp32 weights, `V` is an L×DV row-major fp32 value matrix; returns DV
    fp32 context values. (The weights come from softmax, which stays float64 in
    the math model; given the weights, this accumulation is bit-exact.)"""
    out = []
    for k in range(DV):
        p = [f32(f32(w[j]) * f32(V[j][k])) for j in range(L)]
        acc = p[0]
        for j in range(1, L):
            acc = f32(f32(acc) + f32(p[j]))
        out.append(f32(acc))
    return out


def av_context_bits(wb, Vb):
    """av_context over 32-bit patterns: wb is L patterns, Vb is L*DV row-major
    patterns (V[j][k] at index j*DV+k). Returns DV 32-bit patterns."""
    w = [frombits(u) for u in wb]
    V = [[frombits(Vb[j * DV + k]) for k in range(DV)] for j in range(L)]
    return [bits(c) for c in av_context(w, V)]


# ---- softmax numerical-stabilization prep (the exp-free, bit-exact part) ------ #
LS = 8  # scores per softmax row tile


def rowmax_sub(x):
    """Subtract the row maximum from a length-LS score vector — the numerically-
    stable softmax pre-step (so the largest logit becomes 0 and exp() can't
    overflow). Fixed datapath order:
        m    = max_i x_i        (sequential fp32 max, RISC-V fmax ordering; a new
                                 element replaces the running max only when strictly
                                 greater, so ties keep the earlier index)
        y_j  = x_j - m          (fp32 subtract, exact negation)
    Defined for finite / -inf scores (the attention domain incl. causal -inf mask);
    NaN inputs are out of scope. Returns LS fp32 values (each <= 0)."""
    m = f32(x[0])
    for i in range(1, LS):
        if f32(x[i]) > f32(m):
            m = f32(x[i])
    return [f32(f32(x[j]) - f32(m)) for j in range(LS)]


def rowmax_sub_bits(xb):
    """rowmax_sub over LS 32-bit input patterns, returning LS 32-bit patterns."""
    x = [frombits(u) for u in xb]
    return [bits(c) for c in rowmax_sub(x)]


def softmax_norm(e):
    """Normalise a length-LS vector of (already exp'd) weights into probabilities
    p_j = e_j / sum_i e_i — the divide half of softmax. Fixed datapath order:
        s   = ((e_0 + e_1) + …) + e_{LS-1}   (fp32 fixed-order sum)
        inv = 1 / s                          (correctly-rounded fp32 reciprocal)
        p_j = e_j * inv                      (fp32 scale)
    `e` elements are fp32 values (the exp() itself stays in the float64 math model,
    not bit-matched); returns LS fp32 probabilities. Bit-exact given e."""
    acc = f32(e[0])
    for i in range(1, LS):
        acc = f32(f32(acc) + f32(e[i]))
    inv = f32(f32(1.0) / f32(acc))
    return [f32(f32(e[j]) * inv) for j in range(LS)]


def softmax_norm_bits(eb):
    """softmax_norm over LS 32-bit input patterns, returning LS 32-bit patterns."""
    e = [frombits(u) for u in eb]
    return [bits(c) for c in softmax_norm(e)]
