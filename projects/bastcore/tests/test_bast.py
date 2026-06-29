import numpy as np

import bast_matmul as g
from bast_matmul_model import SystolicArray


def test_matmul_vs_numpy():
    rng = np.random.default_rng(0)
    A = rng.standard_normal((8, 16)).astype(np.float32)
    B = rng.standard_normal((16, 12)).astype(np.float32)
    ref = (g.round_bf16(A).astype(np.float64) @ g.round_bf16(B).astype(np.float64))
    out = g.matmul(A, B)
    # norm-wise relative error is the right accuracy metric (per-element blows up
    # on near-zero outputs from cancellation). bf16 ~2^-8 per element.
    rel = np.linalg.norm(out - ref) / np.linalg.norm(ref)
    assert rel < 0.02


def test_identity():
    A = g.round_bf16(np.array([[1.0, 2.0, 4.0], [0.5, 0.25, 8.0]], dtype=np.float32))
    I = np.eye(3, dtype=np.float32)
    out = g.matmul(A, I)
    assert np.allclose(out, A)


def test_pymodel_equals_golden():
    rng = np.random.default_rng(1)
    A = rng.standard_normal((6, 10)).astype(np.float32)
    B = rng.standard_normal((10, 7)).astype(np.float32)
    arr = SystolicArray(tile=16)
    out = arr.matmul(A, B)
    assert np.array_equal(out, g.matmul(A, B))
    assert arr.macs == 6 * 7 * 10
    assert arr.cycles == 10


def test_int8_dot():
    # max-magnitude products
    assert g.int8_dot([127], [127]) == 127 * 127
    assert g.int8_dot([0x80], [0x80]) == 128 * 128          # -128 * -128 = 16384
    assert g.int8_dot([0x80], [127]) == (-128 * 127) & 0xFFFFFFFF
    assert g.int8_dot([1, 0xFF], [1, 1]) == 0               # 1 + (-1) = 0
    # accumulation of many max products stays correct (no premature saturation)
    assert g.int8_dot([127] * 100, [127] * 100) == 127 * 127 * 100
    assert g.int8_dot([0x80] * 50, [127] * 50) == (-128 * 127 * 50) & 0xFFFFFFFF


def test_int8_matmul():
    # 2x2 result of all-ones K=4: each cell = 4
    Ab = [[1, 1, 1, 1], [1, 1, 1, 1]]
    Bb = [[1, 1], [1, 1], [1, 1], [1, 1]]
    out = g.int8_matmul(Ab, Bb, 4, 2, 2)
    assert out == [[4, 4], [4, 4]]
    # signed: row of -1 (0xFF) times col of 1 -> -K
    Ab = [[0xFF, 0xFF]]
    Bb = [[1], [1]]
    assert g.int8_matmul(Ab, Bb, 2, 1, 1) == [[(-2) & 0xFFFFFFFF]]
    # consistency with int8_dot per cell
    Ab = [[3, 0xFE, 7], [0x80, 5, 0x7F]]
    Bb = [[2, 0xFF], [0x7F, 1], [4, 0x80]]
    out = g.int8_matmul(Ab, Bb, 3, 2, 2)
    for i in range(2):
        for j in range(2):
            assert out[i][j] == g.int8_dot(Ab[i], [Bb[k][j] for k in range(3)])
