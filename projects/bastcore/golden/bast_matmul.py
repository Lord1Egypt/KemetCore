"""BastCore golden reference — BF16 tensor core (matmul).

BF16 inputs, FP32 accumulation (the standard tensor-core datapath): each product
is bf16xbf16 rounded into fp32, accumulated in fp32. Mirrors what the hardware
MAC array computes.
"""
import numpy as np


def round_bf16(x):
    """Round an fp32 array to bf16 (stored as fp32), round-to-nearest-even."""
    x = np.asarray(x, dtype=np.float32)
    u = x.view(np.uint32).astype(np.uint64)
    lsb = (u >> np.uint64(16)) & np.uint64(1)
    u = (u + np.uint64(0x7FFF) + lsb) >> np.uint64(16) << np.uint64(16)
    out = u.astype(np.uint32).view(np.float32)
    # keep non-finite values intact (bias add could corrupt them)
    nf = ~np.isfinite(x)
    out[nf] = x[nf]
    return out


def matmul(A, B):
    """BF16 matmul with FP32 accumulate. A:(M,K) B:(K,N) -> (M,N) fp32."""
    A = round_bf16(A)
    B = round_bf16(B)
    M, K = A.shape
    K2, N = B.shape
    assert K == K2, "inner dimensions must match"
    out = np.zeros((M, N), dtype=np.float32)
    for k in range(K):
        # bf16 product rounded to fp32, then fp32 accumulate
        prod = round_bf16(A[:, k:k + 1] * B[k:k + 1, :])
        out = (out + prod).astype(np.float32)
    return out
