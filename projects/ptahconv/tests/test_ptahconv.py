import numpy as np

import ptah_conv as g
from ptah_conv_model import TiledConv


def test_conv_vs_reference():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((2, 3, 8, 8)).astype(np.float32)
    w = rng.standard_normal((4, 3, 3, 3)).astype(np.float32)
    a = g.conv2d_naive(x, w, stride=1, pad=1)
    b = g.conv2d_im2col(x, w, stride=1, pad=1)
    assert np.allclose(a, b, atol=1e-4)
    assert a.shape == (2, 4, 8, 8)


def test_stride_pad():
    rng = np.random.default_rng(1)
    x = rng.standard_normal((1, 2, 7, 7)).astype(np.float32)
    w = rng.standard_normal((3, 2, 3, 3)).astype(np.float32)
    a = g.conv2d_naive(x, w, stride=2, pad=1)
    b = g.conv2d_im2col(x, w, stride=2, pad=1)
    assert a.shape == (1, 3, 4, 4)
    assert np.allclose(a, b, atol=1e-4)


def test_pymodel_equals_golden():
    rng = np.random.default_rng(2)
    x = rng.standard_normal((1, 3, 6, 6)).astype(np.float32)
    w = rng.standard_normal((5, 3, 3, 3)).astype(np.float32)
    ref = g.conv2d_im2col(x, w, stride=1, pad=0)
    tc = TiledConv(tm=4, tn=4, tk=4)
    out = tc.conv2d(x, w, stride=1, pad=0)
    assert np.allclose(out, ref, atol=1e-4)
    # OH*OW=16 outputs, Cout=5, K=27 -> exact MAC count
    assert tc.macs == 16 * 5 * 27


def test_dot_seq():
    import struct
    import numpy as np
    import ptah_conv as g

    def f2b(x):
        return int(np.frombuffer(struct.pack("<f", np.float32(x)), np.uint32)[0])

    def b2f(u):
        return float(np.frombuffer(struct.pack("<I", u), np.float32)[0])

    assert b2f(g.dot_seq([f2b(1.0)], [f2b(2.0)])) == 2.0
    assert b2f(g.dot_seq([f2b(1.0)] * 8, [f2b(1.0)] * 8)) == 8.0
    # sequential order: matches an explicit Python fp32 fold (NOT numpy pairwise sum)
    rng = np.random.default_rng(7)
    for _ in range(50):
        K = int(rng.integers(1, 20))
        a = rng.standard_normal(K).astype(np.float32)
        b = rng.standard_normal(K).astype(np.float32)
        acc = np.float32(0.0)
        for i in range(K):
            acc = np.float32(acc + np.float32(a[i] * b[i]))
        got = g.dot_seq([f2b(x) for x in a], [f2b(x) for x in b])
        assert got == int(np.frombuffer(acc.tobytes(), np.uint32)[0])


def test_matmul_seq():
    import struct
    import numpy as np
    import ptah_conv as g

    def f2b(x):
        return int(np.frombuffer(struct.pack("<f", np.float32(x)), np.uint32)[0])

    def b2f(u):
        return float(np.frombuffer(struct.pack("<I", u), np.float32)[0])

    A = [[f2b(1.0), f2b(2.0)], [f2b(3.0), f2b(4.0)]]
    B = [[f2b(5.0), f2b(6.0)], [f2b(7.0), f2b(8.0)]]
    C = g.matmul_seq(A, B, 2, 2, 2)
    assert b2f(C[0][0]) == 1 * 5 + 2 * 7
    assert b2f(C[0][1]) == 1 * 6 + 2 * 8
    assert b2f(C[1][0]) == 3 * 5 + 4 * 7
    assert b2f(C[1][1]) == 3 * 6 + 4 * 8
    # each output equals the sequential dot of its row/col
    rng = np.random.default_rng(11)
    M, N, K = 3, 4, 5
    A = [[f2b(x) for x in rng.standard_normal(K).astype(np.float32)] for _ in range(M)]
    B = [[f2b(x) for x in rng.standard_normal(N).astype(np.float32)] for _ in range(K)]
    C = g.matmul_seq(A, B, M, N, K)
    for i in range(M):
        for j in range(N):
            assert C[i][j] == g.dot_seq(A[i], [B[k][j] for k in range(K)])
