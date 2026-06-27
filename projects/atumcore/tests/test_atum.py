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
