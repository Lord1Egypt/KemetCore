"""ImentetCore pymodel — flash-style tiled attention (online softmax).

Processes K/V in blocks, maintaining a running max and running denominator so the
full score matrix is never materialised (the hardware-friendly form). Matches the
golden attention to floating-point tolerance.
"""
import numpy as np

import imentet_attention as g


def flash_attention(Q, K, V, block=8, mask=None):
    Q = np.asarray(Q, np.float64)
    K = np.asarray(K, np.float64)
    V = np.asarray(V, np.float64)
    Lq, d = Q.shape
    Lk, dv = V.shape
    scale = 1.0 / np.sqrt(d)
    out = np.zeros((Lq, dv), np.float64)
    m = np.full((Lq, 1), -np.inf)           # running max
    l = np.zeros((Lq, 1))                    # running denominator
    for j0 in range(0, Lk, block):
        j1 = min(j0 + block, Lk)
        s = (Q @ K[j0:j1].T) * scale         # (Lq, b)
        if mask is not None:
            s = s + mask[:, j0:j1]
        m_new = np.maximum(m, np.max(s, axis=1, keepdims=True))
        p = np.exp(s - m_new)                 # (Lq, b)
        alpha = np.exp(m - m_new)             # rescale prior accumulation
        l = alpha * l + np.sum(p, axis=1, keepdims=True)
        out = alpha * out + p @ V[j0:j1]
        m = m_new
    return out / l
