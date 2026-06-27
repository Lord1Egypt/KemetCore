"""PtahConv pymodel — tiled im2col dataflow.

Streams the lowered matmul in (TM x TN) output tiles over a TK contraction tile,
modelling how the systolic array consumes the convolution. Result is bit-identical
to the golden im2col path; also reports MAC count.
"""
import numpy as np

import ptah_conv as g


class TiledConv:
    def __init__(self, tm=8, tn=8, tk=8):
        self.tm, self.tn, self.tk = tm, tn, tk
        self.macs = 0

    def conv2d(self, x, w, stride=1, pad=0):
        w = np.asarray(w, np.float32)
        Cout, KH, KW = w.shape[0], w.shape[2], w.shape[3]
        cols, OH, OW = g.im2col(x, KH, KW, stride, pad)
        N = cols.shape[0]
        wmat = w.reshape(Cout, -1).T
        K = wmat.shape[0]
        out = np.zeros((N, Cout, OH, OW), np.float32)
        for n in range(N):
            A = cols[n]                       # (M, K), M = OH*OW
            M = A.shape[0]
            Y = np.zeros((M, Cout), np.float32)
            for i0 in range(0, M, self.tm):
                for j0 in range(0, Cout, self.tn):
                    for k0 in range(0, K, self.tk):
                        a = A[i0:i0 + self.tm, k0:k0 + self.tk]
                        b = wmat[k0:k0 + self.tk, j0:j0 + self.tn]
                        Y[i0:i0 + a.shape[0], j0:j0 + b.shape[1]] += (a @ b).astype(np.float32)
                        self.macs += a.shape[0] * a.shape[1] * b.shape[1]
            out[n] = Y.T.reshape(Cout, OH, OW)
        return out
