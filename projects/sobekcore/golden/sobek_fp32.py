"""SobekCore fp32 datapath primitives — the hardware-accurate building blocks the
Moller-Trumbore intersector is assembled from.

The math reference in `sobek_raytri.py` runs in float64 (the ideal answer). The
*hardware* evaluates the same algebra in IEEE-754 single precision with a fixed
evaluation order, so these primitives define that fp32 order exactly and are the
bit-exact golden the RTL (sobek_dot3.sv, …) is checked against. Every step is a
correctly-rounded fp32 operation (numpy float32 == hapi_fp32_mul / hapi_fp32_add).
"""
import numpy as np


def f32(x):
    return np.float32(x)


def bits(x):
    """fp32 value -> 32-bit pattern."""
    return int(np.float32(x).view(np.uint32))


def frombits(u):
    """32-bit pattern -> fp32 value."""
    return np.uint32(u & 0xFFFFFFFF).view(np.float32)


def dot3(a, b):
    """3-element fp32 dot product, evaluated left-to-right the way the datapath
    does: p_i = a_i * b_i (fp32), then acc = ((p0 + p1) + p2), each add fp32.
    Inputs are fp32 values; returns the fp32 result."""
    p0 = f32(a[0]) * f32(b[0])
    p1 = f32(a[1]) * f32(b[1])
    p2 = f32(a[2]) * f32(b[2])
    acc = f32(p0) + f32(p1)
    acc = f32(acc) + f32(p2)
    return f32(acc)


def dot3_bits(ab, bb):
    """dot3 over 32-bit input patterns, returning the 32-bit result pattern."""
    a = [frombits(u) for u in ab]
    b = [frombits(u) for u in bb]
    return bits(dot3(a, b))
