"""AtumCore golden reference — RISC-V Vector (RVV) subset.

A small length-agnostic vector machine: a vector register file, vsetvl semantics
(VL = min(avl, VLMAX)), integer + fp element ops, masked execution, and reductions.
Integer elements are 32-bit (wrap on overflow); fp ops use fp32.
"""
import numpy as np

VLEN = 256
ELEN = 32
VLMAX = VLEN // ELEN          # 8 elements per vector at SEW=32
NREGS = 32
U32 = (1 << 32) - 1


class VectorUnit:
    def __init__(self):
        self.vreg = [np.zeros(VLMAX, dtype=np.uint32) for _ in range(NREGS)]
        self.vl = VLMAX

    # -- configuration ----------------------------------------------------- #
    def vsetvl(self, avl):
        self.vl = min(avl, VLMAX)
        return self.vl

    # -- helpers ----------------------------------------------------------- #
    def load(self, vd, data):
        a = np.zeros(VLMAX, dtype=np.uint32)
        n = min(len(data), VLMAX)
        a[:n] = np.asarray(data, dtype=np.int64).astype(np.uint32)[:n]
        self.vreg[vd] = a

    def load_f32(self, vd, data):
        a = np.zeros(VLMAX, dtype=np.float32)
        n = min(len(data), VLMAX)
        a[:n] = np.asarray(data, dtype=np.float32)[:n]
        self.vreg[vd] = a.view(np.uint32)

    def read(self, vd):
        return self.vreg[vd][:self.vl].copy()

    def read_f32(self, vd):
        return self.vreg[vd].view(np.float32)[:self.vl].copy()

    def _active(self, mask):
        if mask is None:
            return np.ones(VLMAX, dtype=bool)
        m = np.zeros(VLMAX, dtype=bool)
        m[:len(mask)] = np.asarray(mask, dtype=bool)
        return m

    def _wr_int(self, vd, result, mask):
        act = self._active(mask)
        out = self.vreg[vd].copy()
        idx = np.arange(VLMAX) < self.vl
        sel = act & idx
        out[sel] = (result.astype(np.uint64) & U32).astype(np.uint32)[sel]
        self.vreg[vd] = out

    # -- integer ops (vd = vs1 OP vs2) ------------------------------------- #
    def _binop(self, vd, vs1, vs2, fn, mask):
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        self._wr_int(vd, fn(a, b), mask)

    def vadd(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a + b, mask)

    def vsub(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a - b, mask)

    def vmul(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a * b, mask)

    def vand(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a & b, mask)

    def vor(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a | b, mask)

    def vxor(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a ^ b, mask)

    def vsll(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: a << (b & 31), mask)

    def vsrl(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2,
                    lambda a, b: (a & U32) >> (b & 31), mask)

    def vmacc(self, vd, vs1, vs2, mask=None):
        """vd += vs1 * vs2 (fused multiply-accumulate)."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        acc = self.vreg[vd].astype(np.int64)
        self._wr_int(vd, acc + a * b, mask)

    def vminu(self, vd, vs1, vs2, mask=None):
        a, b = self.vreg[vs1], self.vreg[vs2]               # unsigned
        self._wr_int(vd, np.where(a < b, a, b).astype(np.int64), mask)

    def vmaxu(self, vd, vs1, vs2, mask=None):
        a, b = self.vreg[vs1], self.vreg[vs2]
        self._wr_int(vd, np.where(a > b, a, b).astype(np.int64), mask)

    def vmin(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].astype(np.int32)                 # signed compare
        b = self.vreg[vs2].astype(np.int32)
        self._wr_int(vd, np.where(a < b, self.vreg[vs1], self.vreg[vs2]).astype(np.int64), mask)

    def vmax(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].astype(np.int32)
        b = self.vreg[vs2].astype(np.int32)
        self._wr_int(vd, np.where(a > b, self.vreg[vs1], self.vreg[vs2]).astype(np.int64), mask)

    # -- fp ops ------------------------------------------------------------ #
    def vfadd(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].view(np.float32)
        b = self.vreg[vs2].view(np.float32)
        self._wr_f32(vd, a + b, mask)

    def vfmul(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].view(np.float32)
        b = self.vreg[vs2].view(np.float32)
        self._wr_f32(vd, a * b, mask)

    def _wr_f32(self, vd, result, mask):
        act = self._active(mask)
        idx = np.arange(VLMAX) < self.vl
        sel = act & idx
        out = self.vreg[vd].view(np.float32).copy()
        out[sel] = result.astype(np.float32)[sel]
        self.vreg[vd] = out.view(np.uint32)

    # -- reductions -------------------------------------------------------- #
    def vredsum(self, vs, mask=None):
        act = self._active(mask)[:self.vl]
        return int(self.vreg[vs][:self.vl].astype(np.int64)[act].sum() & U32)

    def vredmax(self, vs, mask=None):
        act = self._active(mask)[:self.vl]
        vals = self.vreg[vs][:self.vl].astype(np.int64)[act]
        return int(vals.max())
