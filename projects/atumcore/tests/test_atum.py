import numpy as np

import atum_rvv as g
from atum_rvv_model import VectorEngine, axpy, LANES


def test_vadd_vmul():
    vu = g.VectorUnit()
    a = [1, 2, 3, 4, 5, 6, 7, 8]
    b = [10, 20, 30, 40, 50, 60, 70, 80]
    vu.load(1, a)
    vu.load(2, b)
    vu.vadd(3, 1, 2)
    vu.vmul(4, 1, 2)
    assert list(vu.read(3)) == [x + y for x, y in zip(a, b)]
    assert list(vu.read(4)) == [x * y for x, y in zip(a, b)]


def test_vminmax():
    vu = g.VectorUnit()
    a = [1, -5 & 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 100, 0, 0xFFFFFFFF, 7]
    b = [2, 3, 0x7FFFFFFE, 1, 100, 0xFFFFFFFF, 0, 7]
    vu.load(1, a); vu.load(2, b)
    vu.vminu(3, 1, 2); vu.vmaxu(4, 1, 2)
    vu.vmin(5, 1, 2);  vu.vmax(6, 1, 2)
    import numpy as np
    A = np.array(a, np.uint32); B = np.array(b, np.uint32)
    assert list(vu.read(3)) == list(np.where(A < B, A, B))
    assert list(vu.read(4)) == list(np.where(A > B, A, B))
    As = A.astype(np.int32); Bs = B.astype(np.int32)
    assert list(vu.read(5)) == list(np.where(As < Bs, A, B))
    assert list(vu.read(6)) == list(np.where(As > Bs, A, B))


def test_vrsub():
    vu = g.VectorUnit()
    a = [1, 100, 0xFFFFFFFF, 5, 0, 0x80000000, 7, 9]
    b = [2, 3, 0, 5, 9, 1, 0, 8]
    vu.load(1, a); vu.load(2, b)
    vu.vrsub(3, 1, 2)
    assert list(vu.read(3)) == [(y - x) & 0xFFFFFFFF for x, y in zip(a, b)]


def test_vsra():
    import numpy as np
    vu = g.VectorUnit()
    a = [0x80000000, 0xFFFFFFFF, 0x7FFFFFFF, 16, -8 & 0xFFFFFFFF, 1, 0, 0xDEADBEEF]
    b = [1, 4, 1, 2, 3, 0, 31, 8]
    vu.load(1, a); vu.load(2, b)
    vu.vsra(3, 1, 2)
    A = np.array(a, np.uint32).astype(np.int32); B = np.array(b, np.uint32)
    assert list(vu.read(3)) == list((A >> (B & 31)).astype(np.uint32))


def test_vmacc():
    vu = g.VectorUnit()
    vu.load(1, [2, 3, 4, 5, 6, 7, 8, 9])
    vu.load(2, [1, 1, 1, 1, 2, 2, 2, 2])
    vu.load(3, [100] * 8)            # accumulator
    vu.vmacc(3, 1, 2)               # 100 + v1*v2
    expected = [100 + a * b for a, b in zip([2, 3, 4, 5, 6, 7, 8, 9],
                                            [1, 1, 1, 1, 2, 2, 2, 2])]
    assert list(vu.read(3)) == expected


def test_masked():
    vu = g.VectorUnit()
    vu.load(1, [1, 2, 3, 4, 5, 6, 7, 8])
    vu.load(2, [10, 10, 10, 10, 10, 10, 10, 10])
    vu.load(3, [0, 0, 0, 0, 0, 0, 0, 0])
    mask = [1, 0, 1, 0, 1, 0, 1, 0]
    vu.vadd(3, 1, 2, mask=mask)
    out = list(vu.read(3))
    assert out == [11, 0, 13, 0, 15, 0, 17, 0]


def test_vmask_compare():
    vu = g.VectorUnit()
    #            eq   gt   lt(u) lt(s,neg) eq  gt    lt    eq
    a = [5, 9, 1, 0x80000000, 7, 0x7FFFFFFF, 2, 5]
    b = [5, 3, 4, 0x00000001, 7, 0x00000001, 9, 5]
    vu.load(1, a); vu.load(2, b)
    # vmseq: lanes equal -> 0,4,7
    assert list(vu.vmseq(1, 2)) == [1, 0, 0, 0, 1, 0, 0, 1]
    # vmsltu: unsigned a<b -> lane2 (1<4), lane6 (2<9); 0x80000000<1 unsigned false
    assert list(vu.vmsltu(1, 2)) == [0, 0, 1, 0, 0, 0, 1, 0]
    # vmslt: signed a<b -> lane2, lane3 (0x80000000 is negative < 1), lane6
    assert list(vu.vmslt(1, 2)) == [0, 0, 1, 1, 0, 0, 1, 0]
    # vmsne is the complement of vmseq
    assert list(vu.vmsne(1, 2)) == [0, 1, 1, 1, 0, 1, 1, 0]


def test_vmask_vl_and_mask():
    vu = g.VectorUnit()
    vu.load(1, [1, 1, 1, 1, 1, 1, 1, 1])
    vu.load(2, [1, 1, 1, 1, 1, 1, 1, 1])
    vu.vl = 4                              # only first 4 lanes are body-active
    mask = [1, 0, 1, 1, 1, 1, 1, 1]        # lane1 masked off
    # equal everywhere, but tail (>=vl) and masked lanes read 0
    assert list(vu.vmseq(1, 2, mask=mask)) == [1, 0, 1, 1, 0, 0, 0, 0]
    # vmsle <= holds on equal -> same active pattern
    assert list(vu.vmsle(1, 2, mask=mask)) == [1, 0, 1, 1, 0, 0, 0, 0]


def test_vmask_logic():
    vu = g.VectorUnit()
    m1 = [1, 1, 0, 0, 1, 0, 1, 0]
    m2 = [1, 0, 1, 0, 1, 1, 0, 0]
    assert list(vu.vmand(m1, m2))  == [a & b for a, b in zip(m1, m2)]
    assert list(vu.vmor(m1, m2))   == [a | b for a, b in zip(m1, m2)]
    assert list(vu.vmxor(m1, m2))  == [a ^ b for a, b in zip(m1, m2)]
    assert list(vu.vmnand(m1, m2)) == [1 - (a & b) for a, b in zip(m1, m2)]
    assert list(vu.vmnor(m1, m2))  == [1 - (a | b) for a, b in zip(m1, m2)]
    assert list(vu.vmxnor(m1, m2)) == [1 - (a ^ b) for a, b in zip(m1, m2)]
    assert list(vu.vmandn(m1, m2)) == [a & (1 - b) for a, b in zip(m1, m2)]
    assert list(vu.vmorn(m1, m2))  == [a | (1 - b) for a, b in zip(m1, m2)]


def test_vmask_logic_vl():
    vu = g.VectorUnit()
    vu.vl = 3
    z = [0] * 8
    # vmnand body would be 1 everywhere; only first vl=3 bits written, tail = 0
    assert list(vu.vmnand(z, z)) == [1, 1, 1, 0, 0, 0, 0, 0]


def test_vmpopc():
    vu = g.VectorUnit()
    m = [1, 0, 1, 1, 0, 0, 1, 0]            # 4 bits set, first at lane 0
    assert vu.vcpop(m) == 4
    assert vu.vfirst(m) == 0
    assert vu.vcpop([0] * 8) == 0
    assert vu.vfirst([0] * 8) == -1         # none set -> -1
    m2 = [0, 0, 0, 1, 0, 0, 0, 0]
    assert vu.vfirst(m2) == 3
    # vl gating: a set bit beyond vl is not counted
    vu.vl = 2
    assert vu.vcpop(m) == 1                  # only lane0 within vl
    assert vu.vfirst(m) == 0
    # v0.t mask gates lane0 off -> first becomes lane... none within vl=2 now
    assert vu.vfirst(m, mask=[0, 1, 1, 1, 1, 1, 1, 1]) == -1


def test_viota_vid():
    vu = g.VectorUnit()
    # viota = exclusive prefix sum of the mask
    m = [1, 0, 1, 1, 0, 1, 0, 0]
    assert list(vu.viota(m)) == [0, 1, 1, 2, 3, 3, 4, 4]
    # vid = element index
    assert list(vu.vid()) == [0, 1, 2, 3, 4, 5, 6, 7]
    # vl gating: tail lanes read 0
    vu.vl = 4
    assert list(vu.vid()) == [0, 1, 2, 3, 0, 0, 0, 0]
    assert list(vu.viota(m)) == [0, 1, 1, 2, 0, 0, 0, 0]
    # v0.t-inactive source lanes don't advance the iota count
    vu.vl = 8
    assert list(vu.viota([1, 1, 1, 1, 0, 0, 0, 0],
                         mask=[1, 0, 1, 1, 1, 1, 1, 1])) == [0, 0, 1, 2, 3, 3, 3, 3]


def test_vcompress():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])
    # keep lanes 1,3,5,7 -> packed to front, rest 0
    assert list(vu.vcompress(1, [0, 1, 0, 1, 0, 1, 0, 1])) == [11, 13, 15, 17, 0, 0, 0, 0]
    # keep all -> unchanged
    assert list(vu.vcompress(1, [1] * 8)) == [10, 11, 12, 13, 14, 15, 16, 17]
    # keep none -> all zero
    assert list(vu.vcompress(1, [0] * 8)) == [0] * 8
    # vl gating: mask bits beyond vl are ignored
    vu.vl = 4
    assert list(vu.vcompress(1, [1, 0, 1, 0, 1, 1, 1, 1])) == [10, 12, 0, 0, 0, 0, 0, 0]


def test_vrgather():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])     # source
    vu.load(2, [7, 6, 5, 4, 3, 2, 1, 0])             # reverse index
    assert list(vu.vrgather(1, 2)) == [17, 16, 15, 14, 13, 12, 11, 10]
    # broadcast lane0 + out-of-range index -> 0
    vu.load(2, [0, 0, 99, 3, 8, 1, 2, 0xFFFF])
    assert list(vu.vrgather(1, 2)) == [10, 10, 0, 13, 0, 11, 12, 0]
    # vl gating: idx >= vl reads 0, tail lanes read 0
    vu.vl = 4
    vu.load(2, [3, 2, 1, 0, 0, 0, 0, 0])
    assert list(vu.vrgather(1, 2)) == [13, 12, 11, 10, 0, 0, 0, 0]


def test_vslide():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])
    # slideup by 2: lanes 0,1 -> 0; lane i -> src[i-2]
    assert list(vu.vslideup(1, 2)) == [0, 0, 10, 11, 12, 13, 14, 15]
    # slidedown by 2: lane i -> src[i+2]; lanes sliding past vl -> 0
    assert list(vu.vslidedown(1, 2)) == [12, 13, 14, 15, 16, 17, 0, 0]
    # offset 0 = identity within vl
    assert list(vu.vslideup(1, 0)) == [10, 11, 12, 13, 14, 15, 16, 17]
    # offset >= vl -> all 0
    assert list(vu.vslidedown(1, 8)) == [0] * 8
    # vl gating
    vu.vl = 4
    assert list(vu.vslideup(1, 1)) == [0, 10, 11, 12, 0, 0, 0, 0]
    assert list(vu.vslidedown(1, 1)) == [11, 12, 13, 0, 0, 0, 0, 0]


def test_vmerge():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])     # taken where mask=1
    vu.load(2, [20, 21, 22, 23, 24, 25, 26, 27])     # taken where mask=0
    m = [1, 0, 1, 0, 1, 0, 1, 0]
    assert list(vu.vmerge(1, 2, m)) == [10, 21, 12, 23, 14, 25, 16, 27]
    assert list(vu.vmerge(1, 2, [1] * 8)) == [10, 11, 12, 13, 14, 15, 16, 17]
    assert list(vu.vmerge(1, 2, [0] * 8)) == [20, 21, 22, 23, 24, 25, 26, 27]
    # vl gating
    vu.vl = 3
    assert list(vu.vmerge(1, 2, m)) == [10, 21, 12, 0, 0, 0, 0, 0]


def test_vfsgnj():
    vu = g.VectorUnit()
    #     +1.0       -1.0        +0.0        -2.0
    a = [0x3F800000, 0xBF800000, 0x00000000, 0xC0000000,
         0x7F800000, 0xFF800000, 0x40490FDB, 0x80000000]
    b = [0xBF800000, 0x3F800000, 0x80000000, 0x3F800000,
         0x80000000, 0x00000000, 0xC0000000, 0x7F800000]
    vu.load(1, a); vu.load(2, b)
    # sgnj: sign from b, magnitude from a
    out0 = list(vu.vfsgnj(1, 2, 0))
    for i in range(8):
        exp = (b[i] & 0x80000000) | (a[i] & 0x7FFFFFFF)
        assert out0[i] == exp
    # sgnjn with b==a -> negate a (flip sign of every element)
    vu.load(2, a)
    out1 = list(vu.vfsgnj(1, 2, 1))
    assert out1 == [(x ^ 0x80000000) for x in a]
    # sgnjx with b==a -> abs a (sign cleared)
    out2 = list(vu.vfsgnj(1, 2, 2))
    assert out2 == [(x & 0x7FFFFFFF) for x in a]
    # vl gating
    vu.vl = 4
    assert list(vu.vfsgnj(1, 2, 2))[4:] == [0, 0, 0, 0]


def test_vfminmax():
    import struct

    def fb(x):
        return struct.unpack("<I", struct.pack("<f", x))[0]
    vu = g.VectorUnit()
    a = [fb(1.0), fb(-2.0), fb(3.5), fb(0.0),
         0x7FC00000, fb(5.0), fb(-1.0), 0x7F800000]   # NaN at 4, +inf at 7
    b = [fb(2.0), fb(-1.0), fb(-3.5), 0x80000000,
         fb(9.0), 0x7FC00000, fb(-2.0), fb(100.0)]    # -0 at 3, NaN at 5
    vu.load(1, a); vu.load(2, b)
    mn = list(vu.vfmin(1, 2))
    mx = list(vu.vfmax(1, 2))
    assert mn[0] == fb(1.0) and mx[0] == fb(2.0)
    assert mn[1] == fb(-2.0) and mx[1] == fb(-1.0)
    assert mn[2] == fb(-3.5) and mx[2] == fb(3.5)
    # 0.0 vs -0.0 -> min=-0, max=+0
    assert mn[3] == 0x80000000 and mx[3] == 0x00000000
    # NaN vs number -> the number (both min and max)
    assert mn[4] == fb(9.0) and mx[4] == fb(9.0)
    assert mn[5] == fb(5.0) and mx[5] == fb(5.0)
    # +inf
    assert mn[7] == fb(100.0) and mx[7] == 0x7F800000
    # both NaN -> canonical
    vu.load(1, [0x7FC00000] * 8); vu.load(2, [0x7F800099] * 8)
    assert list(vu.vfmin(1, 2)) == [0x7FC00000] * 8


def test_vfclass():
    vu = g.VectorUnit()
    #     +0          -0          +1(norm)    -1(norm)
    a = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000,
         0x00000001, 0x80000001, 0x7F800000, 0xFF800000]   # +sub,-sub,+inf,-inf
    vu.load(1, a)
    out = list(vu.vfclass(1))
    assert out[0] == (1 << 4)    # +0
    assert out[1] == (1 << 3)    # -0
    assert out[2] == (1 << 6)    # +normal
    assert out[3] == (1 << 1)    # -normal
    assert out[4] == (1 << 5)    # +subnormal
    assert out[5] == (1 << 2)    # -subnormal
    assert out[6] == (1 << 7)    # +inf
    assert out[7] == (1 << 0)    # -inf
    # NaNs: sNaN (bit8) vs qNaN (bit9)
    vu.load(1, [0x7F800001, 0x7FC00000, 0xFF800001, 0xFFC00001, 0, 0, 0, 0])
    out = list(vu.vfclass(1))
    assert out[0] == (1 << 8)    # sNaN (mant MSB 0)
    assert out[1] == (1 << 9)    # qNaN (mant MSB 1)
    assert out[2] == (1 << 8)    # -sNaN still classed as sNaN bit
    assert out[3] == (1 << 9)    # -qNaN
    # vl gating
    vu.vl = 2
    assert list(vu.vfclass(1))[2:] == [0] * 6


def test_vmsbf():
    vu = g.VectorUnit()
    m = [0, 0, 1, 0, 1, 0, 0, 0]            # first set bit at lane 2
    assert list(vu.vmsbf(m)) == [1, 1, 0, 0, 0, 0, 0, 0]   # before first
    assert list(vu.vmsif(m)) == [1, 1, 1, 0, 0, 0, 0, 0]   # up to + incl first
    assert list(vu.vmsof(m)) == [0, 0, 1, 0, 0, 0, 0, 0]   # only first
    # empty mask: sbf/sif fill the body, sof all-0
    z = [0] * 8
    assert list(vu.vmsbf(z)) == [1] * 8
    assert list(vu.vmsif(z)) == [1] * 8
    assert list(vu.vmsof(z)) == [0] * 8
    # vl gating: set bit beyond vl -> treated as empty body
    vu.vl = 4
    assert list(vu.vmsbf([0, 0, 0, 0, 1, 0, 0, 0])) == [1, 1, 1, 1, 0, 0, 0, 0]
    assert list(vu.vmsof([0, 0, 0, 0, 1, 0, 0, 0])) == [0, 0, 0, 0, 0, 0, 0, 0]


def test_vmv():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])
    assert list(vu.vmv_vx(0x99)) == [0x99] * 8          # splat
    assert list(vu.vmv_vv(1)) == [10, 11, 12, 13, 14, 15, 16, 17]   # copy
    # vl gating
    vu.vl = 3
    assert list(vu.vmv_vx(7)) == [7, 7, 7, 0, 0, 0, 0, 0]
    assert list(vu.vmv_vv(1)) == [10, 11, 12, 0, 0, 0, 0, 0]


def test_vslide1():
    vu = g.VectorUnit()
    vu.load(1, [10, 11, 12, 13, 14, 15, 16, 17])
    assert list(vu.vslide1up(1, 99)) == [99, 10, 11, 12, 13, 14, 15, 16]
    assert list(vu.vslide1down(1, 99)) == [11, 12, 13, 14, 15, 16, 17, 99]
    # vl gating: slide1down inserts x at the top *active* lane (vl-1)
    vu.vl = 4
    assert list(vu.vslide1up(1, 99)) == [99, 10, 11, 12, 0, 0, 0, 0]
    assert list(vu.vslide1down(1, 99)) == [11, 12, 13, 99, 0, 0, 0, 0]
    # vl=1: both yield [x]
    vu.vl = 1
    assert list(vu.vslide1up(1, 99))[0] == 99
    assert list(vu.vslide1down(1, 99))[0] == 99


def test_vredsum():
    vu = g.VectorUnit()
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    vu.load(1, data)
    assert vu.vredsum(1) == sum(data)
    assert vu.vredmax(1) == max(data)


def test_vfmul_fp():
    vu = g.VectorUnit()
    x = np.array([1.5, 2.5, -3.0, 0.25, 8.0, -1.0, 4.5, 100.0], np.float32)
    y = np.array([2.0, 2.0, 2.0, 4.0, 0.5, 3.0, 2.0, 0.01], np.float32)
    vu.load_f32(1, x)
    vu.load_f32(2, y)
    vu.vfmul(3, 1, 2)
    assert np.allclose(vu.read_f32(3), x * y)


def test_axpy_stripmined():
    rng = np.random.default_rng(0)
    n = 37                                  # not a multiple of VLMAX (8)
    x = rng.standard_normal(n).astype(np.float32)
    y = rng.standard_normal(n).astype(np.float32)
    a = np.float32(2.5)
    out, eng = axpy(a, x, y)
    assert np.allclose(out, a * x + y, atol=1e-5)
    # 37 elements -> ceil(37/8) = 5 strip-mining iterations
    assert eng.vsetvl(0) == 0
    assert eng.ops == 5 * 2                  # vfmul + vfadd per iteration


def test_vfcvt_roundtrip_and_saturate():
    import struct
    fb = lambda f: struct.unpack("<I", struct.pack("<f", f))[0]
    vu = g.VectorUnit()
    # int32 -> fp32 (op 0): exact small ints + RNE for >2**24.
    vu.vreg[1] = np.array([0, 1, 0xFFFFFFFF, 0x80000000, 16777216,
                           16777217, 0x40000000, 0x7FFFFFFF], np.uint32)
    out = vu.vfcvt(1, 0)
    assert out[0] == 0
    assert struct.unpack("<f", struct.pack("<I", int(out[1])))[0] == 1.0
    assert struct.unpack("<f", struct.pack("<I", int(out[2])))[0] == -1.0   # signed -1
    assert struct.unpack("<f", struct.pack("<I", int(out[3])))[0] == -2147483648.0
    # uint32 -> fp32 (op 1): 0xFFFFFFFF is positive 4294967295 -> rounds to 2**32.
    out_u = vu.vfcvt(1, 1)
    assert struct.unpack("<f", struct.pack("<I", int(out_u[2])))[0] == 4294967296.0
    # fp32 -> int32 RNE (op 2): ties to even, saturation on Inf/NaN/overflow.
    vu.vreg[1] = np.array([fb(2.5), fb(3.5), fb(-2.5), fb(1e30),
                           fb(-1e30), 0x7FC00000, fb(1.4), fb(-0.5)], np.uint32)
    s = vu.vfcvt(1, 2)
    assert int(s[0]) == 2 and int(s[1]) == 4 and (int(s[2]) & 0xFFFFFFFF) == ((-2) & 0xFFFFFFFF)
    assert int(s[3]) == 0x7FFFFFFF                  # +overflow -> INT32_MAX
    assert int(s[4]) == 0x80000000                  # -overflow -> INT32_MIN
    assert int(s[5]) == 0x7FFFFFFF                  # NaN -> INT32_MAX
    assert int(s[6]) == 1 and int(s[7]) == 0
    # fp32 -> uint32: negative saturates to 0; truncation differs from RNE.
    u = vu.vfcvt(1, 3)
    assert int(u[2]) == 0 and int(u[4]) == 0
    t = vu.vfcvt(1, 4)                               # rtz signed
    assert int(t[1]) == 3 and int(t[6]) == 1        # 3.5 trunc -> 3, 1.4 -> 1


def test_vfsub_fp():
    vu = g.VectorUnit()
    x = np.array([1.5, 2.5, -3.0, 0.25, 8.0, -1.0, 4.5, 100.0], np.float32)
    y = np.array([2.0, 2.0, 2.0, 4.0, 0.5, 3.0, 2.0, 0.01], np.float32)
    vu.load_f32(1, x)
    vu.load_f32(2, y)
    vu.vfsub(3, 1, 2)
    assert np.allclose(vu.read_f32(3), x - y)
    vu.vfrsub(4, 1, 2)
    assert np.allclose(vu.read_f32(4), y - x)        # reverse operand order


def test_vfdiv_fp():
    vu = g.VectorUnit()
    x = np.array([1.0, 3.0, -8.0, 1.0, 7.0, -2.0, 9.0, 1.0], np.float32)
    y = np.array([2.0, 3.0, 4.0, 0.0, 2.0, 8.0, 3.0, 0.0], np.float32)  # y[3]=1/0 inf
    vu.load_f32(1, x)
    vu.load_f32(2, y)
    vu.vfdiv(3, 1, 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        exp = x / y
    got = vu.read_f32(3)
    assert np.array_equal(got[np.isfinite(exp)], exp[np.isfinite(exp)])  # exact RNE
    assert np.isinf(got[3])                                              # 1.0/0.0 -> inf
    vu.vfrdiv(4, 1, 2)                                # reverse: vd = y / x
    with np.errstate(divide="ignore", invalid="ignore"):
        rexp = y / x
    assert np.array_equal(vu.read_f32(4), rexp.astype(np.float32))


def test_vfsqrt_fp():
    vu = g.VectorUnit()
    x = np.array([0.0, 1.0, 4.0, 9.0, 25.0, 2.0, 100.0, 0.25], np.float32)
    vu.load_f32(1, x)
    vu.vfsqrt(2, 1)
    assert np.array_equal(vu.read_f32(2), np.sqrt(x))        # exact RNE
    # negative -> NaN, +inf -> +inf
    z = np.array([-1.0, np.inf, -0.0, 16.0, 0.0, 1e30, 1e-30, 49.0], np.float32)
    vu.load_f32(3, z)
    with np.errstate(invalid="ignore"):
        vu.vfsqrt(4, 3)
    got = vu.read_f32(4)
    assert np.isnan(got[0]) and np.isinf(got[1]) and got[1] > 0
    assert got[3] == 4.0 and got[7] == 7.0


def test_vmfcmp_fp():
    vu = g.VectorUnit()
    x = np.array([1.0, 2.0, np.nan, 0.0, -0.0, np.inf, -1.0, 3.0], np.float32)
    y = np.array([1.0, 1.0, 1.0, -0.0, 0.0, np.inf, 1.0, 3.0], np.float32)
    vu.load_f32(1, x)
    vu.load_f32(2, y)
    assert list(vu.vmfeq(1, 2)) == [1, 0, 0, 1, 1, 1, 0, 1]   # +0==-0, NaN!=, inf==inf
    assert list(vu.vmfne(1, 2)) == [0, 1, 1, 0, 0, 0, 1, 0]   # NaN -> ne true
    assert list(vu.vmflt(1, 2)) == [0, 0, 0, 0, 0, 0, 1, 0]
    assert list(vu.vmfle(1, 2)) == [1, 0, 0, 1, 1, 1, 1, 1]
    assert list(vu.vmfge(1, 2)) == [1, 1, 0, 1, 1, 1, 0, 1]


def test_vfmacc_fp():
    vu = g.VectorUnit()
    x = np.array([1.5, 2.0, -3.0, 0.5, 4.0, 1.0, 2.5, 10.0], np.float32)
    y = np.array([2.0, 3.0, 2.0, 8.0, 0.25, 7.0, 4.0, 0.1], np.float32)
    acc = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], np.float32)
    vu.load_f32(1, x)
    vu.load_f32(2, y)
    vu.load_f32(3, acc)
    vu.vfmacc(3, 1, 2)                       # acc += x*y, fused
    assert np.allclose(vu.read_f32(3), acc + x * y, atol=1e-5)
    vu.load_f32(3, acc)
    vu.vfmsac(3, 1, 2)                       # x*y - acc
    assert np.allclose(vu.read_f32(3), x * y - acc, atol=1e-5)
    vu.load_f32(3, acc)
    vu.vfnmacc(3, 1, 2)                      # -(x*y) - acc
    assert np.allclose(vu.read_f32(3), -(x * y) - acc, atol=1e-5)
    vu.load_f32(3, acc)
    vu.vfnmsac(3, 1, 2)                      # -(x*y) + acc
    assert np.allclose(vu.read_f32(3), -(x * y) + acc, atol=1e-5)


def test_vsadd_saturate():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 1,
                           5, 0x80000000, 100, 0xFFFFFFFF], np.uint32)
    vu.vreg[2] = np.array([1, 1, 0xFFFFFFFF, 2,
                           3, 1, 0xFFFFFFFF, 0xFFFFFFFF], np.uint32)
    vu.vsaddu(3, 1, 2)
    assert int(vu.vreg[3][0]) == 0xFFFFFFFF          # unsigned overflow -> UMAX
    assert int(vu.vreg[3][3]) == 3                    # 1+2, no sat
    vu.vsadd(4, 1, 2)
    assert int(vu.vreg[4][1]) == 0x7FFFFFFF           # INT_MAX + 1 -> INT_MAX
    assert int(vu.vreg[4][2]) == 0x80000000           # INT_MIN + (-1) -> INT_MIN
    vu.vssubu(5, 1, 2)
    assert int(vu.vreg[5][3]) == 0                     # 1 - 2 -> 0 (clamp)
    assert int(vu.vreg[5][0]) == 0xFFFFFFFE            # 0xFFFFFFFF - 1
    vu.vssub(6, 1, 2)
    assert int(vu.vreg[6][5]) == 0x80000000           # INT_MIN - 1 -> INT_MIN


def test_vsmul_q31():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([0x80000000, 0x7FFFFFFF, 0x40000000, 0xC0000000,
                           0, 0x7FFFFFFF, 0x40000000, 1], np.uint32)
    vu.vreg[2] = np.array([0x80000000, 0x40000000, 0x40000000, 0x40000000,
                           0x7FFFFFFF, 0x7FFFFFFF, 0x80000000, 1], np.uint32)
    vu.vsmul(3, 1, 2)
    # -1 * -1 (Q31) = +1.0 -> saturates to INT32_MAX
    assert int(vu.vreg[3][0]) == 0x7FFFFFFF
    # 0.5 * 0.5 (Q31) = 0.25 -> 0x20000000
    assert int(vu.vreg[3][2]) == 0x20000000
    # 0 * anything = 0
    assert int(vu.vreg[3][4]) == 0
    # cross-check against the golden roundoff formula on all lanes
    a = vu.vreg[1].astype(np.int32).astype(np.int64)
    b = vu.vreg[2].astype(np.int32).astype(np.int64)
    exp = np.clip((a * b + (1 << 30)) >> 31, -(2**31), 2**31 - 1).astype(np.uint32)
    assert list(vu.vreg[3]) == list(exp)


def test_vssr_rounding():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([3, 1, 5, 0xFFFFFFFF, 0x80000000, 6, 2, 8], np.uint32)
    vu.vreg[2] = np.array([1, 1, 1, 1, 2, 0, 1, 4], np.uint32)
    vu.vssrl(3, 1, 2)
    # rnu: 3>>1 -> 2, 1>>1 -> 1, 5>>1 -> 3, sh=0 -> identity(6)
    assert int(vu.vreg[3][0]) == 2
    assert int(vu.vreg[3][1]) == 1
    assert int(vu.vreg[3][2]) == 3
    assert int(vu.vreg[3][5]) == 6
    assert int(vu.vreg[3][3]) == 0x80000000          # 0xFFFFFFFF>>1 rnu
    vu.vssra(4, 1, 2)
    # arithmetic: -1 (0xFFFFFFFF) >> 1 rnu -> 0; INT_MIN>>2 rnu
    assert int(vu.vreg[4][3]) == 0
    assert (int(vu.vreg[4][4]) & 0xFFFFFFFF) == ((-(2**31) >> 2) + ((-(2**31) >> 1) & 1)) & 0xFFFFFFFF


def test_vimac_family():
    M = 0xFFFFFFFF
    vu = g.VectorUnit()
    s1 = np.array([2, 3, 4, 5, 0, 7, 0xFFFFFFFF, 10], np.uint32)
    s2 = np.array([10, 10, 10, 10, 10, 10, 2, 10], np.uint32)
    d0 = np.array([1, 1, 1, 1, 1, 1, 1, 1], np.uint32)
    vu.vreg[1], vu.vreg[2], vu.vreg[3] = s1.copy(), s2.copy(), d0.copy()
    vu.vmadd(3, 1, 2)                                    # vd = s1*vd + s2
    exp = ((s1.astype(np.int64) * d0 + s2) & M).astype(np.uint32)
    assert list(vu.vreg[3]) == list(exp)
    vu.vreg[3] = d0.copy()
    vu.vnmsac(3, 1, 2)                                   # vd = vd - s1*s2
    exp = ((d0.astype(np.int64) - s1.astype(np.int64) * s2) & M).astype(np.uint32)
    assert list(vu.vreg[3]) == list(exp)
    vu.vreg[3] = d0.copy()
    vu.vnmsub(3, 1, 2)                                   # vd = s2 - s1*vd
    exp = ((s2.astype(np.int64) - s1.astype(np.int64) * d0) & M).astype(np.uint32)
    assert list(vu.vreg[3]) == list(exp)


def test_vaadd_averaging():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([1, 2, 0xFFFFFFFF, 0xFFFFFFFF, 0x80000000, 10, 0, 4], np.uint32)
    vu.vreg[2] = np.array([2, 2, 1, 0xFFFFFFFF, 0x80000000, 20, 0, 7], np.uint32)
    vu.vaaddu(3, 1, 2)
    # avg(1,2)=2 (rnu of 1.5), avg(0xFFFFFFFF,1) unsigned = 2^31 (no overflow)
    assert int(vu.vreg[3][0]) == 2
    assert int(vu.vreg[3][2]) == 0x80000000
    vu.vaadd(4, 1, 2)
    # signed avg(-1,-1) = -1
    assert int(vu.vreg[4][3]) == 0xFFFFFFFF
    vu.vasub(5, 1, 2)
    # signed avg-diff(-1 - 1) ... cross-check golden formula
    a = vu.vreg[1].astype(np.int32).astype(np.int64)
    b = vu.vreg[2].astype(np.int32).astype(np.int64)
    exp = (((a - b) >> 1) + ((a - b) & 1)).astype(np.uint32)
    assert list(vu.vreg[5]) == list(exp)


def test_vmulh_family():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([0xFFFFFFFF, 0x80000000, 0x40000000, 2,
                           0xFFFFFFFF, 0x7FFFFFFF, 0, 0x10000000], np.uint32)
    vu.vreg[2] = np.array([0xFFFFFFFF, 0x80000000, 0x40000000, 0x80000000,
                           1, 2, 5, 0x10000000], np.uint32)
    vu.vmulh(3, 1, 2)
    # (-1)*(-1) = 1 -> high 32 = 0
    assert int(vu.vreg[3][0]) == 0
    a = vu.vreg[1].astype(np.int32).astype(np.int64)
    b = vu.vreg[2].astype(np.int32).astype(np.int64)
    assert list(vu.vreg[3]) == list(((a * b) >> 32).astype(np.uint32))
    vu.vmulhu(4, 1, 2)
    au = vu.vreg[1].astype(np.uint64); bu = vu.vreg[2].astype(np.uint64)
    assert list(vu.vreg[4]) == list(((au * bu) >> 32).astype(np.uint32))
    # (0xFFFFFFFF * 0xFFFFFFFF) unsigned high = 0xFFFFFFFE
    assert int(vu.vreg[4][0]) == 0xFFFFFFFE
    vu.vmulhsu(5, 1, 2)
    bsu = vu.vreg[2].astype(np.int64)
    assert list(vu.vreg[5]) == list(((a * bsu) >> 32).astype(np.uint32))


def test_vdiv_specialcases():
    vu = g.VectorUnit()
    vu.vreg[1] = np.array([7, 0xFFFFFFFF, 0x80000000, 7, 100, 0x80000000, 1, 10], np.uint32)
    vu.vreg[2] = np.array([0, 3, 0xFFFFFFFF, 2, 0, 0, 0xFFFFFFFF, 3], np.uint32)
    vu.vdivu(3, 1, 2)
    assert int(vu.vreg[3][0]) == 0xFFFFFFFF          # div by zero -> all ones
    vu.vdiv(4, 1, 2)
    assert int(vu.vreg[4][2]) == 0x80000000          # INT_MIN / -1 -> INT_MIN (overflow)
    assert int(vu.vreg[4][1]) == 0                    # -1 / 3 trunc -> 0
    vu.vremu(5, 1, 2)
    assert int(vu.vreg[5][4]) == 100                  # rem by zero -> a
    vu.vrem(6, 1, 2)
    assert int(vu.vreg[6][2]) == 0                     # INT_MIN % -1 -> 0
    assert (int(vu.vreg[6][1]) & 0xFFFFFFFF) == 0xFFFFFFFF  # -1 % 3 -> -1
