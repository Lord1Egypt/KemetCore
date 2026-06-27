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
