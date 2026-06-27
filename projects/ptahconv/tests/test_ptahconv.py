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
