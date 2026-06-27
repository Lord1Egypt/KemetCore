"""ImentetCore golden reference — scaled dot-product attention.

attention(Q,K,V) = softmax(Q Kᵀ / sqrt(d) + mask) V, with a numerically-stable
softmax (subtract row max before exp). Optional causal mask.
"""
import numpy as np


def softmax(x, axis=-1):
    x = np.asarray(x, np.float64)
    m = np.max(x, axis=axis, keepdims=True)
    e = np.exp(x - m)                       # stable: max term becomes exp(0)=1
    return (e / np.sum(e, axis=axis, keepdims=True))


def causal_mask(n):
    """(n,n) additive mask: 0 on/below diagonal, -inf above (future positions)."""
    m = np.zeros((n, n), np.float64)
    m[np.triu_indices(n, k=1)] = -np.inf
    return m


def attention(Q, K, V, mask=None):
    """Q:(Lq,d) K:(Lk,d) V:(Lk,dv) -> (Lq,dv)."""
    Q = np.asarray(Q, np.float64)
    K = np.asarray(K, np.float64)
    V = np.asarray(V, np.float64)
    d = Q.shape[-1]
    scores = (Q @ K.T) / np.sqrt(d)
    if mask is not None:
        scores = scores + mask
    return softmax(scores, axis=-1) @ V
