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
