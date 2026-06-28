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
