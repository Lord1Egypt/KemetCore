"""GebCore pymodel — metadata-driven sparse MAC.

Walks the compressed (values, indices) stream and performs exactly one MAC per
kept lane, so the MAC count is ~half of a dense matmul. Bit-identical to the
golden sparse_matmul.
"""
import numpy as np

import geb_sparse as g


class SparseMAC:
    def __init__(self):
        self.macs = 0

    def matmul(self, A, values, indices):
        A = np.asarray(A, np.float32)
        M = A.shape[0]
        KH, N = values.shape
        out = np.zeros((M, N), np.float32)
        for col in range(N):
            for s in range(KH):
                grp = (s // 2) * 4
                lane = grp + int(indices[s, col])
                out[:, col] += A[:, lane] * values[s, col]
                self.macs += M
        return out.astype(np.float32)
