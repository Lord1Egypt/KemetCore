import numpy as np

import geb_sparse as g
from geb_sparse_model import SparseMAC


def test_sparse_equals_dense():
    rng = np.random.default_rng(0)
    A = rng.standard_normal((6, 16)).astype(np.float32)
    W = rng.standard_normal((16, 8)).astype(np.float32)
    Wp = g.prune_2of4(W)
    values, indices = g.compress_2of4(Wp)
    sparse = g.sparse_matmul(A, values, indices)
    dense = g.dense_matmul(A, Wp)
    assert np.allclose(sparse, dense, atol=1e-4)


def test_compression_metadata():
    # column with a clear top-2 per group of 4
    W = np.array([[5.0], [1.0], [4.0], [2.0],
                  [0.1], [9.0], [0.2], [8.0]], dtype=np.float32)
    Wp = g.prune_2of4(W)
    # group 0 keeps 5,4 ; group 1 keeps 9,8
    assert set(np.nonzero(Wp[:4, 0])[0]) == {0, 2}
    assert set(np.nonzero(Wp[4:, 0])[0]) == {1, 3}
    values, indices = g.compress_2of4(Wp)
    assert values.shape == (4, 1)
    # all kept indices are within 0..3
    assert indices.min() >= 0 and indices.max() <= 3


def test_macs_halved():
    rng = np.random.default_rng(1)
    A = rng.standard_normal((4, 16)).astype(np.float32)
    W = rng.standard_normal((16, 5)).astype(np.float32)
    Wp = g.prune_2of4(W)
    values, indices = g.compress_2of4(Wp)
    mac = SparseMAC()
    out = mac.matmul(A, values, indices)
    assert np.allclose(out, g.sparse_matmul(A, values, indices))
    # dense would be M*K*N = 4*16*5 = 320; sparse is exactly half: 4*8*5 = 160
    assert mac.macs == 4 * 8 * 5


def test_prune_group():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    # distinct magnitudes: keep the two largest
    mask, kept = g.prune_group([f2b(1.0), f2b(2.0), f2b(3.0), f2b(4.0)])
    assert mask == 0b1100 and [i for i, _ in kept] == [2, 3]
    # magnitude ties broken toward the lower lane index
    mask, kept = g.prune_group([f2b(5.0), f2b(-5.0), f2b(5.0), f2b(1.0)])
    assert [i for i, _ in kept] == [0, 1]
    # exactly two lanes are always kept
    for _ in range(200):
        bits = [int.from_bytes(np.random.bytes(4), "little") for _ in range(4)]
        mask, kept = g.prune_group(bits)
        assert bin(mask).count("1") == 2 and len(kept) == 2
        assert kept[0][0] < kept[1][0]
