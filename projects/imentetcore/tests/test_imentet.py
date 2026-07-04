import numpy as np

import imentet_attention as g
from imentet_attention_model import flash_attention


def test_attention_vs_reference():
    rng = np.random.default_rng(0)
    Q = rng.standard_normal((5, 8))
    K = rng.standard_normal((7, 8))
    V = rng.standard_normal((7, 4))
    out = g.attention(Q, K, V)
    # independent reference
    scores = Q @ K.T / np.sqrt(8)
    p = np.exp(scores - scores.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    assert np.allclose(out, p @ V, atol=1e-9)
    assert out.shape == (5, 4)


def test_softmax_stable():
    x = np.array([1000.0, 1001.0, 1002.0])    # would overflow naive exp
    s = g.softmax(x)
    assert np.isclose(s.sum(), 1.0)
    assert np.all(np.isfinite(s))
    # shift-invariance
    assert np.allclose(g.softmax(x), g.softmax(x + 12345.0))


def test_flash_equals_golden():
    rng = np.random.default_rng(1)
    Q = rng.standard_normal((6, 16))
    K = rng.standard_normal((20, 16))
    V = rng.standard_normal((20, 5))
    ref = g.attention(Q, K, V)
    out = flash_attention(Q, K, V, block=8)
    assert np.allclose(out, ref, atol=1e-9)


def test_causal_mask():
    rng = np.random.default_rng(2)
    n, d = 6, 8
    Q = rng.standard_normal((n, d))
    K = rng.standard_normal((n, d))
    V = rng.standard_normal((n, d))
    mask = g.causal_mask(n)
    out = g.attention(Q, K, V, mask=mask)
    flash = flash_attention(Q, K, V, block=3, mask=mask)
    assert np.allclose(out, flash, atol=1e-9)
    # row 0 attends only to position 0 -> output equals V[0]
    assert np.allclose(out[0], V[0], atol=1e-9)


def test_fp32_score_order_and_bits():
    """imentet_fp32.score is the fixed-order fp32 datapath the imentet_qk_score RTL
    matches: p_i = q_i*k_i, a left-to-right acc fold, then one multiply by the
    1/sqrt(d) scale — all round-to-nearest fp32."""
    import imentet_fp32 as f

    D = f.D
    # exact small-integer dot: sum_{i<D} i = D(D-1)/2
    assert f.dot(list(range(D)), [1.0] * D) == np.float32(D * (D - 1) // 2)
    # matches an explicit left-to-right fp32 evaluation
    q = [0.1 * i for i in range(D)]
    k = [0.2 * (i + 1) for i in range(D)]
    prods = [np.float32(np.float32(q[i]) * np.float32(k[i])) for i in range(D)]
    acc = prods[0]
    for i in range(1, D):
        acc = np.float32(np.float32(acc) + np.float32(prods[i]))
    assert f.dot(q, k) == acc
    # score applies one more fp32 multiply by the scale
    s = np.float32(1.0 / np.sqrt(D))
    assert f.score(q, k, s) == np.float32(np.float32(acc) * s)
    # bit round-trip helpers are consistent
    for x in (0.0, 1.0, -3.5, 1e20, -1e-20):
        assert f.frombits(f.bits(x)) == np.float32(x)
    # score_bits agrees with score on patterns
    qb = [f.bits(v) for v in q]
    kb = [f.bits(v) for v in k]
    assert f.score_bits(qb, kb, f.bits(s)) == f.bits(f.score(q, k, s))


def test_fp32_av_context_order_and_bits():
    """imentet_fp32.av_context is the fixed-order fp32 datapath imentet_av_context
    matches: per output k, products w[j]*V[j][k] into a left-to-right acc fold."""
    import imentet_fp32 as f

    L, DV = f.L, f.DV
    # picking row 0 with a one-hot weight returns V[0]
    V = [[float(10 * j + k) for k in range(DV)] for j in range(L)]
    w = [1.0] + [0.0] * (L - 1)
    assert f.av_context(w, V) == [np.float32(V[0][k]) for k in range(DV)]
    # matches explicit fixed-order fp32 evaluation
    w = [0.1, 0.2, 0.3, 0.4][:L]
    for k in range(DV):
        prods = [np.float32(np.float32(w[j]) * np.float32(V[j][k])) for j in range(L)]
        acc = prods[0]
        for j in range(1, L):
            acc = np.float32(np.float32(acc) + np.float32(prods[j]))
        assert f.av_context(w, V)[k] == acc
    # av_context_bits agrees
    wb = [f.bits(x) for x in w]
    Vb = [f.bits(V[j][k]) for j in range(L) for k in range(DV)]
    assert f.av_context_bits(wb, Vb) == [f.bits(x) for x in f.av_context(w, V)]
