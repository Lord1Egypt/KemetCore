"""AtumCore pymodel — 8-lane vector engine + strip-mined loops.

Wraps the golden VectorUnit, modelling 8 parallel ALU lanes (one element per lane
per cycle) and providing a strip-mined axpy that processes arbitrary-length arrays
in VLMAX chunks via vsetvl — the length-agnostic RVV programming model.
"""
import numpy as np

import atum_rvv as g

LANES = 8


class VectorEngine(g.VectorUnit):
    def __init__(self):
        super().__init__()
        self.cycles = 0
        self.ops = 0

    def _charge(self):
        # all VLMAX==LANES elements processed in parallel -> 1 cycle/op here
        self.cycles += max(1, self.vl // LANES)
        self.ops += 1

    def vadd(self, *a, **k):
        super().vadd(*a, **k); self._charge()

    def vmul(self, *a, **k):
        super().vmul(*a, **k); self._charge()

    def vmacc(self, *a, **k):
        super().vmacc(*a, **k); self._charge()

    def vfadd(self, *a, **k):
        super().vfadd(*a, **k); self._charge()

    def vfmul(self, *a, **k):
        super().vfmul(*a, **k); self._charge()


def axpy(a, x, y):
    """Strip-mined y = a*x + y over arbitrary-length fp32 arrays."""
    x = np.asarray(x, np.float32)
    y = np.asarray(y, np.float32).copy()
    eng = VectorEngine()
    n = len(x)
    off = 0
    while off < n:
        vl = eng.vsetvl(n - off)
        eng.load_f32(1, x[off:off + vl])           # v1 = x chunk
        eng.load_f32(2, [a] * vl)                   # v2 = scalar a broadcast
        eng.load_f32(3, y[off:off + vl])            # v3 = y chunk
        eng.vfmul(1, 1, 2)                           # v1 = a*x
        eng.vfadd(3, 1, 3)                           # v3 = a*x + y
        y[off:off + vl] = eng.read_f32(3)
        off += vl
    return y, eng
