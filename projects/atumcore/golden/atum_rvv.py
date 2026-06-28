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

    def vsra(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].astype(np.int32)                 # arithmetic shift
        b = self.vreg[vs2]
        self._wr_int(vd, (a >> (b & 31)).astype(np.uint32).astype(np.int64), mask)

    def vrsub(self, vd, vs1, vs2, mask=None):
        self._binop(vd, vs1, vs2, lambda a, b: b - a, mask)

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

    # -- compare ops (vd = mask, 1 bit per lane) --------------------------- #
    def _cmp(self, vs1, vs2, fn, signed, mask):
        """Per-lane compare producing a length-VLMAX 0/1 mask. A lane bit is set
        only when the lane is body-active (i < vl) AND mask-active and the
        comparison holds; inactive/tail lanes read 0 (mask-undisturbed=0 here)."""
        if signed:
            a = self.vreg[vs1].astype(np.int32)
            b = self.vreg[vs2].astype(np.int32)
        else:
            a = self.vreg[vs1]
            b = self.vreg[vs2]
        cmp = fn(a, b)
        act = self._active(mask)
        idx = np.arange(VLMAX) < self.vl
        res = np.zeros(VLMAX, dtype=np.uint8)
        sel = act & idx
        res[sel] = cmp.astype(np.uint8)[sel]
        return res

    def vmseq(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a == b, False, mask)

    def vmsne(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a != b, False, mask)

    def vmsltu(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a < b, False, mask)

    def vmslt(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a < b, True, mask)

    def vmsleu(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a <= b, False, mask)

    def vmsle(self, vs1, vs2, mask=None):
        return self._cmp(vs1, vs2, lambda a, b: a <= b, True, mask)

    # -- mask logical ops (mask = mask OP mask) ---------------------------- #
    def _vmlogic(self, m1, m2, fn):
        """Bitwise logic on two length-VLMAX 0/1 masks. Result bit i = fn(...) for
        i < vl, else 0 (mask ops are unmasked; only the body is written here)."""
        m1 = np.asarray(m1, dtype=np.uint8) & 1
        m2 = np.asarray(m2, dtype=np.uint8) & 1
        res = np.zeros(VLMAX, dtype=np.uint8)
        for i in range(VLMAX):
            if i < self.vl:
                res[i] = fn(int(m1[i]), int(m2[i])) & 1
        return res

    def vmand(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: a & b)

    def vmor(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: a | b)

    def vmxor(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: a ^ b)

    def vmnand(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: ~(a & b))

    def vmnor(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: ~(a | b))

    def vmxnor(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: ~(a ^ b))

    def vmandn(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: a & ~b)      # m1 AND NOT m2

    def vmorn(self, m1, m2):
        return self._vmlogic(m1, m2, lambda a, b: a | ~b)      # m1 OR  NOT m2

    # -- mask reductions (mask -> scalar) ---------------------------------- #
    def vcpop(self, m, mask=None):
        """Population count: number of set bits in m among body-active (i < vl)
        and v0.t-active lanes."""
        act = self._active(mask)
        m = np.asarray(m, dtype=np.uint8) & 1
        return int(sum(1 for i in range(VLMAX)
                       if i < self.vl and act[i] and m[i]))

    def vfirst(self, m, mask=None):
        """Index of the first set bit of m among body-active and v0.t-active
        lanes, or -1 if none."""
        act = self._active(mask)
        m = np.asarray(m, dtype=np.uint8) & 1
        for i in range(VLMAX):
            if i < self.vl and act[i] and m[i]:
                return i
        return -1

    # -- mask -> index vectors --------------------------------------------- #
    def viota(self, m, mask=None):
        """Exclusive prefix-sum of a mask: element i = number of set source-mask
        bits strictly before i (a masked-off source contributes 0). Written only to
        active (i < vl, v0.t) lanes; inactive/tail lanes read 0. Building block for
        vector compress (where to write each kept element)."""
        act = self._active(mask)
        m = np.asarray(m, dtype=np.uint8) & 1
        out = np.zeros(VLMAX, dtype=np.uint32)
        cnt = 0
        for i in range(VLMAX):
            active = (i < self.vl) and bool(act[i])
            if active:
                out[i] = cnt
            if active and m[i]:
                cnt += 1
        return out

    def vid(self, mask=None):
        """Element index: vd[i] = i for active (i < vl, v0.t) lanes, else 0."""
        act = self._active(mask)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl and act[i]:
                out[i] = i
        return out

    # -- compress ---------------------------------------------------------- #
    def vcompress(self, vs, m):
        """Pack the source elements whose compress-mask bit is set (among i < vl)
        contiguously into the low lanes of the result, preserving order; the
        remaining high lanes read 0. This is stream compaction / filter — the kept
        element from source lane i lands at lane viota(m)[i]."""
        m = np.asarray(m, dtype=np.uint8) & 1
        src = self.vreg[vs]
        out = np.zeros(VLMAX, dtype=np.uint32)
        j = 0
        for i in range(VLMAX):
            if i < self.vl and m[i]:
                out[j] = src[i]
                j += 1
        return out

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

    def _vredbit(self, vs, mask, op, ident):
        act = self._active(mask)[:self.vl]
        vals = self.vreg[vs][:self.vl][act]
        acc = ident
        for v in vals:
            acc = op(acc, int(v))
        return acc & U32

    def vredand(self, vs, mask=None):
        return self._vredbit(vs, mask, lambda a, b: a & b, U32)

    def vredor(self, vs, mask=None):
        return self._vredbit(vs, mask, lambda a, b: a | b, 0)

    def vredxor(self, vs, mask=None):
        return self._vredbit(vs, mask, lambda a, b: a ^ b, 0)
