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
