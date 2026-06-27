"""BastCore pymodel — output-stationary systolic MAC array.

Streams K partial products through a tile grid, accumulating in fp32 per output
cell. Bit-identical to the golden matmul; also reports MAC count and cycles.
"""
import numpy as np

import bast_matmul as g


class SystolicArray:
    def __init__(self, tile=16):
        self.tile = tile
        self.macs = 0
        self.cycles = 0

    def matmul(self, A, B):
        A = g.round_bf16(A)
        B = g.round_bf16(B)
        M, K = A.shape
        _, N = B.shape
        out = np.zeros((M, N), dtype=np.float32)
        for k in range(K):
            prod = g.round_bf16(A[:, k:k + 1] * B[k:k + 1, :])
            out = (out + prod).astype(np.float32)
            self.macs += M * N
            self.cycles += 1  # one K-step per cycle (fully parallel M*N grid)
        return out
