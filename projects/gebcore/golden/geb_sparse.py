"""GebCore golden reference — 2:4 structured sparse matmul.

2:4 sparsity: in every contiguous group of 4 weights, at most 2 are non-zero.
We compress weights to (values, indices) keeping the 2 largest-magnitude per
group, then a sparse matmul multiplies only the kept lanes. A dense matmul over
the pruned weights is the cross-check (must be bit-identical).
"""
import numpy as np


def prune_2of4(W):
    """Prune W:(K,N) along K in groups of 4, keeping the 2 largest-|.| per group.

    K must be a multiple of 4. Returns the pruned dense matrix.
    """
    W = np.asarray(W, np.float32).copy()
    K, N = W.shape
    assert K % 4 == 0, "K must be a multiple of 4 for 2:4 sparsity"
    for g0 in range(0, K, 4):
        block = W[g0:g0 + 4, :]                       # (4, N)
        keep = np.argsort(-np.abs(block), axis=0)[:2]  # indices of top-2 per column
        mask = np.zeros_like(block, dtype=bool)
        for col in range(N):
            mask[keep[:, col], col] = True
        W[g0:g0 + 4, :] = np.where(mask, block, np.float32(0.0))
    return W


def compress_2of4(Wp):
    """From a pruned matrix, extract (values, indices) metadata.

    values:(K//2, N) the 2 kept weights per group; indices:(K//2, N) their
    position (0..3) within the group of 4.
    """
    Wp = np.asarray(Wp, np.float32)
    K, N = Wp.shape
    KH = K // 2
    values = np.zeros((KH, N), np.float32)
    indices = np.zeros((KH, N), np.int8)
    for g0 in range(0, K, 4):
        block = Wp[g0:g0 + 4, :]
        out = g0 // 2
        for col in range(N):
            nz = np.nonzero(block[:, col])[0]
            # pad to exactly 2 kept lanes (a zero kept lane is harmless)
            nz = list(nz) + [i for i in range(4) if i not in nz]
            for s in range(2):
                lane = nz[s]
                values[out + s, col] = block[lane, col]
                indices[out + s, col] = lane
    return values, indices


def sparse_matmul(A, values, indices):
    """Compute A @ Wp using only the kept lanes.

    A:(M,K)  values/indices:(K//2,N) -> (M,N).
    """
    A = np.asarray(A, np.float32)
    M, K = A.shape
    KH, N = values.shape
    out = np.zeros((M, N), np.float32)
    for col in range(N):
        for s in range(KH):
            grp = (s // 2) * 4
            lane = grp + int(indices[s, col])
            out[:, col] += A[:, lane] * values[s, col]
    return out.astype(np.float32)


def dense_matmul(A, Wp):
    return (np.asarray(A, np.float32) @ np.asarray(Wp, np.float32)).astype(np.float32)


def prune_group(group):
    """Hardware 2:4 pruner for one group of four fp32 weights given as raw 32-bit
    patterns. Keeps the two largest by IEEE magnitude (sign-cleared unsigned bit
    compare key = b & 0x7FFFFFFF), ties broken toward the LOWER lane index. Returns
    (keep_mask, [(idx0, bits0), (idx1, bits1)]) with idx0 < idx1 (ascending kept
    lanes), matching geb_prune. Deterministic for any bit pattern."""
    bits = [int(g) & 0xFFFFFFFF for g in group]
    key = [b & 0x7FFFFFFF for b in bits]
    keep = []
    for i in range(4):
        rank = sum(1 for j in range(4) if j != i and
                   (key[j] > key[i] or (key[j] == key[i] and j < i)))
        keep.append(rank < 2)
    mask = sum(1 << i for i in range(4) if keep[i])
    kept = [(i, bits[i]) for i in range(4) if keep[i]]
    return mask, kept


def compress_group(group):
    """Compress one pruned group of 4 fp32 values into 2 kept lanes, matching
    compress_2of4's per-column logic: order lanes as [nonzero ascending] ++
    [zero ascending] and take the first two as (value, index) pairs. `group` is a
    list/array of 4 fp32 values; returns (val0, idx0, val1, idx1). A value is
    "nonzero" iff its magnitude bits are set (so +/-0 count as zero, like
    np.nonzero). Bit-exact golden for geb_compress."""
    import numpy as np
    g = [np.float32(x) for x in group]
    nz = [i for i in range(4) if (int(np.float32(g[i]).view(np.uint32)) & 0x7FFFFFFF) != 0]
    zero = [i for i in range(4) if i not in nz]
    order = nz + zero
    i0, i1 = order[0], order[1]
    return g[i0], i0, g[i1], i1
