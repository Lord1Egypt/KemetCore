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


def dot_seq(avec, bvec):
    """Sequential fp32 dot product matching the ptah_mac hardware accumulation
    order (element-by-element, correctly-rounded fp32 mul then add, seeded from
    +0.0). Inputs/outputs are raw fp32 bit patterns. The numpy conv references use
    pairwise/blocked sums and are NOT bit-identical to this sequential order."""
    import struct
    acc = np.float32(0.0)
    for ua, ub in zip(avec, bvec):
        a = np.frombuffer(struct.pack("<I", ua & 0xFFFFFFFF), np.float32)[0]
        b = np.frombuffer(struct.pack("<I", ub & 0xFFFFFFFF), np.float32)[0]
        with np.errstate(over="ignore", invalid="ignore"):
            acc = np.float32(acc + np.float32(a * b))
    return int(np.frombuffer(struct.pack("<f", acc), np.uint32)[0])


def matmul_seq(A, B, M, N, K):
    """Sequential fp32 GEMM C[M][N]=A[M][K]@B[K][N] using dot_seq per output
    element (matches the ptah_gemm hardware). A: M x K, B: K x N raw fp32 bits.
    Returns M x N raw fp32 bit patterns."""
    out = [[0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            out[i][j] = dot_seq([A[i][k] for k in range(K)],
                                [B[k][j] for k in range(K)])
    return out


def conv2d_seq(x_bits, w_bits, Cin, H, W, Cout, KH, KW, stride, pad):
    """Sequential fp32 conv (single batch) matching the ptah_conv2d hardware: each
    output is dot_seq over the receptive field in (ic, ky, kx) order, with implicit
    zero padding (a padded tap contributes 0*w == 0, an exact no-op). x_bits is a
    flat Cin*H*W list of fp32 bit patterns (CHW), w_bits a flat Cout*Cin*KH*KW list
    (Cout,Cin,KH,KW). Returns Cout*OH*OW output bit patterns (CHW)."""
    OH = (H + 2 * pad - KH) // stride + 1
    OW = (W + 2 * pad - KW) // stride + 1
    Z = 0x00000000  # +0.0
    out = []
    for co in range(Cout):
        for oh in range(OH):
            for ow in range(OW):
                avec, bvec = [], []
                for ic in range(Cin):
                    for ky in range(KH):
                        for kx in range(KW):
                            ih = oh * stride + ky - pad
                            iw = ow * stride + kx - pad
                            if 0 <= ih < H and 0 <= iw < W:
                                avec.append(x_bits[(ic * H + ih) * W + iw])
                            else:
                                avec.append(Z)
                            bvec.append(w_bits[((co * Cin + ic) * KH + ky) * KW + kx])
                out.append(dot_seq(avec, bvec))
    return out


def bias_relu(x_bits, bias_bits):
    """The conv epilogue applied elementwise: y = relu(x + bias), fp32. The add is
    one correctly-rounded fp32 add (matches hapi_fp32_add); relu keeps a strictly
    positive finite/Inf result and forces everything else (+/-0, negatives, NaN) to
    +0.0. Inputs/outputs are 32-bit fp32 patterns. Bit-exact golden for the
    ptah_bias_relu datapath."""
    import numpy as np
    x = np.frombuffer(np.uint32(x_bits & 0xFFFFFFFF).tobytes(), np.float32)[0]
    b = np.frombuffer(np.uint32(bias_bits & 0xFFFFFFFF).tobytes(), np.float32)[0]
    s = np.float32(x) + np.float32(b)                       # fp32 add (may be NaN/Inf)
    u = int(np.float32(s).view(np.uint32))
    sign = (u >> 31) & 1
    is_nan = ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0
    positive_nonzero = (sign == 0) and ((u & 0x7FFFFFFF) != 0) and not is_nan
    return u if positive_nonzero else 0x00000000


def maxpool2x2(a_bits, b_bits, c_bits, d_bits):
    """2x2 max-pooling over four fp32 lanes: return the maximum by IEEE total order
    (monotonic key k = x ^ (x[31] ? 0xFFFFFFFF : 0x80000000), so -0 < +0 and the
    usual signed ordering holds). Inputs/outputs are 32-bit fp32 patterns. This is
    a plain total-order max (no fmin/fmax NaN special-casing); the bit-exact golden
    for ptah_maxpool."""
    def key(u):
        u &= 0xFFFFFFFF
        return u ^ (0xFFFFFFFF if (u >> 31) & 1 else 0x80000000)

    def mx(x, y):
        return x if key(x) >= key(y) else y

    return mx(mx(a_bits & 0xFFFFFFFF, b_bits & 0xFFFFFFFF),
              mx(c_bits & 0xFFFFFFFF, d_bits & 0xFFFFFFFF))
