"""AtumCore golden reference — RISC-V Vector (RVV) subset.

A small length-agnostic vector machine: a vector register file, vsetvl semantics
(VL = min(avl, VLMAX)), integer + fp element ops, masked execution, and reductions.
Integer elements are 32-bit (wrap on overflow); fp ops use fp32.
"""
import os
import struct
import sys

import numpy as np

VLEN = 256
ELEN = 32
VLMAX = VLEN // ELEN          # 8 elements per vector at SEW=32
NREGS = 32
U32 = (1 << 32) - 1

# Single-rounded fp32 FMA shared with HapiCore (the RTL composes the verified
# hapi_fp32_fma, so the golden references the SAME reference to stay bit-exact).
_HAPI_GOLDEN = os.path.join(os.path.dirname(__file__), '..', '..', 'hapicore', 'golden')
if _HAPI_GOLDEN not in sys.path:
    sys.path.insert(0, _HAPI_GOLDEN)
from hapi_fpu import fp_fma as _hapi_fp_fma  # noqa: E402


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

    # -- saturating fixed-point add/sub ------------------------------------ #
    def vsaddu(self, vd, vs1, vs2, mask=None):
        """Unsigned saturating add: clamp a+b to 2**32-1."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        self._wr_int(vd, np.minimum(a + b, U32), mask)

    def vsadd(self, vd, vs1, vs2, mask=None):
        """Signed saturating add: clamp a+b to [-2**31, 2**31-1]."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        self._wr_int(vd, np.clip(a + b, -(2**31), 2**31 - 1), mask)

    def vssubu(self, vd, vs1, vs2, mask=None):
        """Unsigned saturating sub: clamp a-b low to 0."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        self._wr_int(vd, np.maximum(a - b, 0), mask)

    def vssub(self, vd, vs1, vs2, mask=None):
        """Signed saturating sub: clamp a-b to [-2**31, 2**31-1]."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        self._wr_int(vd, np.clip(a - b, -(2**31), 2**31 - 1), mask)

    def vsmul(self, vd, vs1, vs2, mask=None):
        """Signed Q31 fractional multiply: roundoff_signed(a*b, 31) then saturate to
        the signed 32-bit range (rounding = round-to-nearest, ties up)."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        prod = a * b
        r = (prod + (1 << 30)) >> 31
        self._wr_int(vd, np.clip(r, -(2**31), 2**31 - 1), mask)

    def _vssr(self, vs1, vs2, arith):
        """Rounding right shift (round-to-nearest, ties up). value=vs1, shamt=vs2&31."""
        vals = self.vreg[vs1]
        shs = self.vreg[vs2] & 31
        out = np.zeros(VLMAX, dtype=np.int64)
        for i in range(VLMAX):
            v = int(vals[i])
            if arith and (v & 0x80000000):
                v -= (1 << 32)                         # interpret as signed
            d = int(shs[i])
            out[i] = v if d == 0 else (v >> d) + ((v >> (d - 1)) & 1)
        return out

    def vssrl(self, vd, vs1, vs2, mask=None):
        """Logical rounding shift-right (unsigned value)."""
        self._wr_int(vd, self._vssr(vs1, vs2, False), mask)

    def vssra(self, vd, vs1, vs2, mask=None):
        """Arithmetic rounding shift-right (signed value)."""
        self._wr_int(vd, self._vssr(vs1, vs2, True), mask)

    def vnmsac(self, vd, vs1, vs2, mask=None):
        """vd -= vs1*vs2 (integer multiply-subtract, modular 2^32)."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        c = self.vreg[vd].astype(np.int64)
        self._wr_int(vd, c - a * b, mask)

    def vmadd(self, vd, vs1, vs2, mask=None):
        """vd = vs1*vd + vs2 (vd is the multiplicand; modular 2^32)."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        c = self.vreg[vd].astype(np.int64)
        self._wr_int(vd, a * c + b, mask)

    def vnmsub(self, vd, vs1, vs2, mask=None):
        """vd = vs2 - vs1*vd (modular 2^32)."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        c = self.vreg[vd].astype(np.int64)
        self._wr_int(vd, b - a * c, mask)

    @staticmethod
    def _avg(v):
        """Round-to-nearest-ties-up halving of an exact integer: (v >> 1) + (v & 1)."""
        return (v >> 1) + (v & 1)

    def vaaddu(self, vd, vs1, vs2, mask=None):
        """Unsigned averaging add: (a + b) >> 1, rounded (no overflow)."""
        a = self.vreg[vs1].astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)
        self._wr_int(vd, self._avg(a + b), mask)

    def vaadd(self, vd, vs1, vs2, mask=None):
        """Signed averaging add: (a + b) >> 1, rounded."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        self._wr_int(vd, self._avg(a + b), mask)

    def vasub(self, vd, vs1, vs2, mask=None):
        """Signed averaging difference: (a - b) >> 1, rounded."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        self._wr_int(vd, self._avg(a - b), mask)

    def vmulh(self, vd, vs1, vs2, mask=None):
        """Signed*signed multiply, high 32 bits of the 64-bit product."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int32).astype(np.int64)
        self._wr_int(vd, (a * b) >> 32, mask)

    def vmulhu(self, vd, vs1, vs2, mask=None):
        """Unsigned*unsigned multiply, high 32 bits."""
        a = self.vreg[vs1].astype(np.uint64)
        b = self.vreg[vs2].astype(np.uint64)
        self._wr_int(vd, ((a * b) >> 32).astype(np.int64), mask)

    def vmulhsu(self, vd, vs1, vs2, mask=None):
        """Signed(vs1)*unsigned(vs2) multiply, high 32 bits."""
        a = self.vreg[vs1].astype(np.int32).astype(np.int64)
        b = self.vreg[vs2].astype(np.int64)              # zero-extended (non-negative)
        self._wr_int(vd, (a * b) >> 32, mask)

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

    # -- mask set-before/including/only first ------------------------------ #
    def _vmsbif(self, m, op):
        """RVV mask manip relative to the first set bit f of m (within vl):
        op=0 vmsbf (set bits before f), 1 vmsif (set up to and including f),
        2 vmsof (set only f). If no bit is set: sbf/sif fill the body with 1,
        sof yields all 0. Tail lanes read 0."""
        m = np.asarray(m, dtype=np.uint8) & 1
        out = np.zeros(VLMAX, dtype=np.uint8)
        f = -1
        for i in range(VLMAX):
            if i < self.vl and m[i]:
                f = i
                break
        for i in range(VLMAX):
            if i < self.vl:
                if op == 0:
                    out[i] = 1 if (f == -1 or i < f) else 0
                elif op == 1:
                    out[i] = 1 if (f == -1 or i <= f) else 0
                else:
                    out[i] = 1 if (f != -1 and i == f) else 0
        return out

    def vmsbf(self, m):
        return self._vmsbif(m, 0)

    def vmsif(self, m):
        return self._vmsbif(m, 1)

    def vmsof(self, m):
        return self._vmsbif(m, 2)

    # -- scalar/vector moves ----------------------------------------------- #
    def vmv_vx(self, x):
        """Broadcast (splat) a scalar to every active lane: vd[i] = x for i < vl,
        else 0."""
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = np.uint32(x & U32)
        return out

    def vmv_vv(self, vs):
        """Vector copy: vd[i] = vs[i] for i < vl, else 0."""
        a = self.vreg[vs].astype(np.uint32)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = a[i]
        return out

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

    # -- gather ------------------------------------------------------------ #
    def vrgather(self, vs, idxreg):
        """Vector register gather (arbitrary permutation): vd[i] = vs[idx[i]] where
        idx = vreg[idxreg]. An index >= vl reads 0; tail lanes (i >= vl) read 0.
        General data-motion primitive (table lookup / permute / shuffle)."""
        src = self.vreg[vs]
        idx = self.vreg[idxreg]
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                k = int(idx[i])
                out[i] = src[k] if k < self.vl else 0
        return out

    # -- slides ------------------------------------------------------------ #
    def vslideup(self, vs, off):
        """Slide elements toward higher lanes by a scalar offset: vd[i] = vs[i-off]
        for off <= i < vl; lanes below off and the tail read 0."""
        src = self.vreg[vs]
        off = int(off)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if off <= i < self.vl:
                out[i] = src[i - off]
        return out

    def vslidedown(self, vs, off):
        """Slide elements toward lower lanes by a scalar offset: vd[i] = vs[i+off]
        for i < vl when i+off < vl, else 0 (elements slid in from past vl are 0)."""
        src = self.vreg[vs]
        off = int(off)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                j = i + off
                out[i] = src[j] if j < self.vl else 0
        return out

    def vslide1up(self, vs, x):
        """Slide up by 1, inserting scalar x at lane 0: vd[0]=x, vd[i]=vs[i-1]
        for 0 < i < vl. Tail lanes read 0."""
        src = self.vreg[vs]
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = np.uint32(x & U32) if i == 0 else src[i - 1]
        return out

    def vslide1down(self, vs, x):
        """Slide down by 1, inserting scalar x at the top active lane: vd[vl-1]=x,
        vd[i]=vs[i+1] for i < vl-1. Tail lanes read 0."""
        src = self.vreg[vs]
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = np.uint32(x & U32) if i == self.vl - 1 else src[i + 1]
        return out

    # -- merge / select ---------------------------------------------------- #
    def vmerge(self, vs1, vs2, m):
        """Mask-driven element select: vd[i] = vs1[i] if m[i] else vs2[i], for
        i < vl (tail reads 0). The data consumer of the mask toolkit — picks
        between two sources per lane (e.g. blend the result of a predicated op)."""
        a = self.vreg[vs1]
        b = self.vreg[vs2]
        m = np.asarray(m, dtype=np.uint8) & 1
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = a[i] if m[i] else b[i]
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

    def vfsub(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].view(np.float32)
        b = self.vreg[vs2].view(np.float32)
        self._wr_f32(vd, a - b, mask)

    def vfrsub(self, vd, vs1, vs2, mask=None):
        a = self.vreg[vs1].view(np.float32)
        b = self.vreg[vs2].view(np.float32)
        self._wr_f32(vd, b - a, mask)

    def _wr_f32(self, vd, result, mask):
        act = self._active(mask)
        idx = np.arange(VLMAX) < self.vl
        sel = act & idx
        out = self.vreg[vd].view(np.float32).copy()
        out[sel] = result.astype(np.float32)[sel]
        self.vreg[vd] = out.view(np.uint32)

    # -- fp fused multiply-add (vd = vs1*vs2 +/- vd) ----------------------- #
    @staticmethod
    def _fma_bits(abits, bbits, cbits):
        a = struct.unpack('<f', struct.pack('<I', abits & U32))[0]
        b = struct.unpack('<f', struct.pack('<I', bbits & U32))[0]
        c = struct.unpack('<f', struct.pack('<I', cbits & U32))[0]
        r = _hapi_fp_fma(a, b, c, 'fp32')                 # single-rounded fp32
        return struct.unpack('<I', struct.pack('<f', np.float32(r)))[0]

    def vfmacc(self, vd, vs1, vs2, mask=None):
        """vd = vs1*vs2 + vd (fused, one rounding). vd is the accumulator."""
        a = self.vreg[vs1].astype(np.uint32)
        b = self.vreg[vs2].astype(np.uint32)
        c = self.vreg[vd].astype(np.uint32)
        res = np.array([self._fma_bits(int(a[i]), int(b[i]), int(c[i]))
                        for i in range(VLMAX)], dtype=np.uint32)
        self._wr_int(vd, res.astype(np.int64), mask)

    def vfmsac(self, vd, vs1, vs2, mask=None):
        """vd = vs1*vs2 - vd (fused) == fma(vs1, vs2, -vd)."""
        a = self.vreg[vs1].astype(np.uint32)
        b = self.vreg[vs2].astype(np.uint32)
        c = self.vreg[vd].astype(np.uint32) ^ np.uint32(0x80000000)
        res = np.array([self._fma_bits(int(a[i]), int(b[i]), int(c[i]))
                        for i in range(VLMAX)], dtype=np.uint32)
        self._wr_int(vd, res.astype(np.int64), mask)

    def vfnmacc(self, vd, vs1, vs2, mask=None):
        """vd = -(vs1*vs2) - vd (fused) == fma(-vs1, vs2, -vd)."""
        a = self.vreg[vs1].astype(np.uint32) ^ np.uint32(0x80000000)
        b = self.vreg[vs2].astype(np.uint32)
        c = self.vreg[vd].astype(np.uint32) ^ np.uint32(0x80000000)
        res = np.array([self._fma_bits(int(a[i]), int(b[i]), int(c[i]))
                        for i in range(VLMAX)], dtype=np.uint32)
        self._wr_int(vd, res.astype(np.int64), mask)

    def vfnmsac(self, vd, vs1, vs2, mask=None):
        """vd = -(vs1*vs2) + vd (fused) == fma(-vs1, vs2, vd)."""
        a = self.vreg[vs1].astype(np.uint32) ^ np.uint32(0x80000000)
        b = self.vreg[vs2].astype(np.uint32)
        c = self.vreg[vd].astype(np.uint32)
        res = np.array([self._fma_bits(int(a[i]), int(b[i]), int(c[i]))
                        for i in range(VLMAX)], dtype=np.uint32)
        self._wr_int(vd, res.astype(np.int64), mask)

    # -- fp compare (vd = mask, 1 bit per lane) ---------------------------- #
    def _fcmp(self, vs1, vs2, fn, mask):
        """Per-lane fp32 compare producing a length-VLMAX 0/1 mask. numpy fp compares
        give IEEE ordered/unordered semantics (NaN -> all False except !=; +0 == -0).
        A bit is set only for a body-active (i < vl) AND mask-active lane."""
        a = self.vreg[vs1].view(np.float32)
        b = self.vreg[vs2].view(np.float32)
        cmp = fn(a, b)
        act = self._active(mask)
        idx = np.arange(VLMAX) < self.vl
        res = np.zeros(VLMAX, dtype=np.uint8)
        sel = act & idx
        res[sel] = cmp.astype(np.uint8)[sel]
        return res

    def vmfeq(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.equal, mask)

    def vmfne(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.not_equal, mask)

    def vmflt(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.less, mask)

    def vmfle(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.less_equal, mask)

    def vmfgt(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.greater, mask)

    def vmfge(self, vs1, vs2, mask=None):
        return self._fcmp(vs1, vs2, np.greater_equal, mask)

    # -- fp sign injection ------------------------------------------------- #
    def vfsgnj(self, vs1, vs2, op):
        """Float sign injection: result = {sign, exponent+mantissa of vs1}, where the
        sign comes from op: 0=sgnj (sign of vs2), 1=sgnjn (NOT sign of vs2),
        2=sgnjx (sign(vs1) XOR sign(vs2)). Pure bit ops — the hardware behind fp
        copysign / negate (sgnjn vs2=vs1) / abs (sgnjx vs2=vs1). Tail lanes read 0."""
        a = self.vreg[vs1].astype(np.uint32)
        b = self.vreg[vs2].astype(np.uint32)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                mag = int(a[i]) & 0x7FFFFFFF
                asign = (int(a[i]) >> 31) & 1
                bsign = (int(b[i]) >> 31) & 1
                s = (bsign, bsign ^ 1, asign ^ bsign)[op]
                out[i] = (s << 31) | mag
        return out

    # -- fp min / max ------------------------------------------------------ #
    @staticmethod
    def _fp_isnan(x):
        return ((x >> 23) & 0xFF) == 0xFF and (x & 0x7FFFFF) != 0

    @staticmethod
    def _fp_key(x):
        # monotonic float->uint key: real-value order == unsigned key order, and
        # -0 maps below +0 (so min/max give the IEEE-recommended signed-zero result).
        return ((~x) & 0xFFFFFFFF) if (x >> 31) & 1 else (x | 0x80000000)

    def _vfmm(self, vs1, vs2, want_max):
        a = self.vreg[vs1].astype(np.uint32)
        b = self.vreg[vs2].astype(np.uint32)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                ai, bi = int(a[i]), int(b[i])
                an, bn = self._fp_isnan(ai), self._fp_isnan(bi)
                if an and bn:
                    out[i] = 0x7FC00000              # canonical quiet NaN
                elif an:
                    out[i] = bi                      # NaN propagation: pick the number
                elif bn:
                    out[i] = ai
                else:
                    ka, kb = self._fp_key(ai), self._fp_key(bi)
                    if want_max:
                        out[i] = ai if ka >= kb else bi
                    else:
                        out[i] = ai if ka <= kb else bi
        return out

    def vfmin(self, vs1, vs2):
        return self._vfmm(vs1, vs2, want_max=False)

    def vfmax(self, vs1, vs2):
        return self._vfmm(vs1, vs2, want_max=True)

    # -- fp classify ------------------------------------------------------- #
    @staticmethod
    def _fp_class(x):
        """RVV vfclass 10-bit class of an fp32 bit pattern:
        bit0 -inf, 1 -normal, 2 -subnormal, 3 -0, 4 +0, 5 +subnormal,
        6 +normal, 7 +inf, 8 signalling NaN, 9 quiet NaN."""
        sign = (x >> 31) & 1
        exp = (x >> 23) & 0xFF
        mant = x & 0x7FFFFF
        if exp == 0xFF:
            if mant == 0:
                return (1 << 0) if sign else (1 << 7)          # -inf / +inf
            return (1 << 9) if (mant >> 22) & 1 else (1 << 8)  # qNaN / sNaN
        if exp == 0:
            if mant == 0:
                return (1 << 3) if sign else (1 << 4)          # -0 / +0
            return (1 << 2) if sign else (1 << 5)              # -sub / +sub
        return (1 << 1) if sign else (1 << 6)                  # -normal / +normal

    def vfclass(self, vs):
        a = self.vreg[vs].astype(np.uint32)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                out[i] = self._fp_class(int(a[i]))
        return out

    # -- int <-> fp conversion (vfcvt) ------------------------------------- #
    @staticmethod
    def _i2f(x, signed):
        """Convert a 32-bit integer (signed or unsigned per `signed`) to its fp32
        bit pattern, rounding the magnitude to nearest, ties-to-even (RNE). Mirrors
        the hardware: take |x|, find its MSB, keep 24 significant bits, RNE-round the
        rest (carry may bump the exponent). 32-bit ints fit fp32's 8-bit exponent so
        no overflow to Inf is possible. This is vfcvt.f.x (signed) / vfcvt.f.xu."""
        x &= U32
        if signed and (x >> 31) & 1:
            sign = 1
            mag = (-x) & U32          # 0x80000000 negates to itself = magnitude 2**31
        else:
            sign = 0
            mag = x
        if mag == 0:
            return 0
        msb = mag.bit_length() - 1    # 0..31
        exp = msb
        if msb <= 23:
            frac = (mag << (23 - msb)) & 0x7FFFFF
        else:
            sh = msb - 23             # 1..8
            keep = mag >> sh          # 24-bit significand (leading 1 + 23)
            round_bit = (mag >> (sh - 1)) & 1
            sticky = 1 if (mag & ((1 << (sh - 1)) - 1)) else 0
            if round_bit and (sticky or (keep & 1)):
                keep += 1
                if keep == (1 << 24):  # rounding carried out -> renormalise
                    keep >>= 1
                    exp += 1
            frac = keep & 0x7FFFFF
        return ((sign << 31) | ((exp + 127) << 23) | frac) & U32

    @staticmethod
    def _f2i(bits, signed, truncate):
        """Convert an fp32 bit pattern to a 32-bit integer (signed/unsigned per
        `signed`), rounding to nearest-ties-to-even (or toward zero if `truncate`),
        with out-of-range / NaN saturation per the RVV vfcvt rules: NaN -> the max
        representable; +Inf / too-large positive -> max; -Inf / too-small negative ->
        min (0 for unsigned). This is vfcvt[.rtz].x.f (signed) / .xu.f (unsigned)."""
        from fractions import Fraction
        sign = (bits >> 31) & 1
        exp = (bits >> 23) & 0xFF
        mant = bits & 0x7FFFFF
        posmax = 0x7FFFFFFF if signed else 0xFFFFFFFF
        negmax = 0x80000000 if signed else 0
        if exp == 0xFF:
            if mant != 0:
                return posmax                      # NaN -> max for both
            return negmax if sign else posmax      # +/- Inf
        if exp == 0:
            full, e = mant, -126                   # subnormal (or zero)
        else:
            full, e = (1 << 23) | mant, exp - 127
        if full == 0:
            return 0
        val = Fraction(full, 1 << 23) * (Fraction(2) ** e)   # positive magnitude
        m = int(val) if truncate else round(val)   # trunc-toward-0 / RNE
        if signed:
            if not sign:
                return posmax if m > 0x7FFFFFFF else m
            return negmax if m > 0x80000000 else ((-m) & U32)
        if sign:
            return 0                               # negative -> unsigned saturates to 0
        return posmax if m > 0xFFFFFFFF else m

    def vfcvt(self, vs, op):
        """Vector int<->fp32 convert. op selects the variant:
        0 vfcvt.f.x (int32->fp32), 1 vfcvt.f.xu (uint32->fp32),
        2 vfcvt.x.f (fp32->int32 RNE), 3 vfcvt.xu.f (fp32->uint32 RNE),
        4 vfcvt.rtz.x.f (fp32->int32 trunc), 5 vfcvt.rtz.xu.f (fp32->uint32 trunc).
        Tail lanes (i >= vl) read 0."""
        a = self.vreg[vs].astype(np.uint32)
        out = np.zeros(VLMAX, dtype=np.uint32)
        for i in range(VLMAX):
            if i < self.vl:
                x = int(a[i])
                if op == 0:
                    out[i] = self._i2f(x, signed=True)
                elif op == 1:
                    out[i] = self._i2f(x, signed=False)
                elif op == 2:
                    out[i] = self._f2i(x, signed=True, truncate=False)
                elif op == 3:
                    out[i] = self._f2i(x, signed=False, truncate=False)
                elif op == 4:
                    out[i] = self._f2i(x, signed=True, truncate=True)
                elif op == 5:
                    out[i] = self._f2i(x, signed=False, truncate=True)
        return out

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
