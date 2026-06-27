"""NeithCore pymodel — staged NTT butterfly datapath.

Exposes the NTT as explicit log2(N) butterfly stages (n/2 butterflies each), which
is the hardware pipeline structure. Result is bit-identical to the golden NTT.
"""
import neith_mlkem as g

N = g.N
LOG2N = N.bit_length() - 1
BUTTERFLIES_PER_STAGE = N // 2


class NttPipeline:
    def __init__(self):
        self.stages = 0
        self.butterflies = 0

    def forward(self, a):
        """Negacyclic forward NTT with explicit stage accounting."""
        pre = [a[i] * g._PSI_POW[i] % g.Q for i in range(N)]
        A = g._bitrev(pre)
        length = 2
        while length <= N:
            wlen = pow(g.OMEGA, N // length, g.Q)
            for i in range(0, N, length):
                w = 1
                half = length // 2
                for k in range(half):
                    u = A[i + k]
                    v = A[i + k + half] * w % g.Q
                    A[i + k] = (u + v) % g.Q
                    A[i + k + half] = (u - v) % g.Q
                    w = w * wlen % g.Q
                    self.butterflies += 1
            self.stages += 1
            length <<= 1
        return A
