"""PtahConv golden reference — direct 2D convolution (NCHW).

Two implementations that must agree:
  conv2d_naive : the obvious 6-nested-loop reference (the truth)
  conv2d_im2col: the im2col + matmul form the hardware actually uses
Supports stride and zero-padding. fp32 throughout.
"""
import numpy as np


def conv2d_naive(x, w, stride=1, pad=0):
    """x:(N,Cin,H,W)  w:(Cout,Cin,KH,KW) -> (N,Cout,OH,OW)."""
    x = np.asarray(x, np.float32)
    w = np.asarray(w, np.float32)
    N, Cin, H, W = x.shape
    Cout, Cin2, KH, KW = w.shape
    assert Cin == Cin2
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    OH = (H + 2 * pad - KH) // stride + 1
    OW = (W + 2 * pad - KW) // stride + 1
    out = np.zeros((N, Cout, OH, OW), np.float32)
    for n in range(N):
        for co in range(Cout):
            for oh in range(OH):
                for ow in range(OW):
                    h0, w0 = oh * stride, ow * stride
                    patch = xp[n, :, h0:h0 + KH, w0:w0 + KW]
                    out[n, co, oh, ow] = np.sum(patch * w[co], dtype=np.float32)
    return out


def im2col(x, KH, KW, stride, pad):
    x = np.asarray(x, np.float32)
    N, Cin, H, W = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    OH = (H + 2 * pad - KH) // stride + 1
    OW = (W + 2 * pad - KW) // stride + 1
    cols = np.zeros((N, OH * OW, Cin * KH * KW), np.float32)
    for n in range(N):
        idx = 0
        for oh in range(OH):
            for ow in range(OW):
                h0, w0 = oh * stride, ow * stride
                patch = xp[n, :, h0:h0 + KH, w0:w0 + KW]
                cols[n, idx] = patch.reshape(-1)
                idx += 1
    return cols, OH, OW


def conv2d_im2col(x, w, stride=1, pad=0):
    """The hardware form: lower to a matmul, then reshape."""
    w = np.asarray(w, np.float32)
    Cout = w.shape[0]
    KH, KW = w.shape[2], w.shape[3]
    cols, OH, OW = im2col(x, KH, KW, stride, pad)
    N = cols.shape[0]
    wmat = w.reshape(Cout, -1).T            # (Cin*KH*KW, Cout)
    out = np.zeros((N, Cout, OH, OW), np.float32)
    for n in range(N):
        y = (cols[n] @ wmat).astype(np.float32)   # (OH*OW, Cout)
        out[n] = y.T.reshape(Cout, OH, OW)
    return out
