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


def cross(a, b):
    """3-D fp32 cross product a x b, each component evaluated as two fp32 products
    then an fp32 subtract (a - b == a + (-b), exact negation) — the order the
    datapath uses:
        c0 = a1*b2 - a2*b1
        c1 = a2*b0 - a0*b2
        c2 = a0*b1 - a1*b0
    Returns three fp32 values."""
    def sub(p, q):
        return f32(f32(p) - f32(q))
    c0 = sub(f32(a[1]) * f32(b[2]), f32(a[2]) * f32(b[1]))
    c1 = sub(f32(a[2]) * f32(b[0]), f32(a[0]) * f32(b[2]))
    c2 = sub(f32(a[0]) * f32(b[1]), f32(a[1]) * f32(b[0]))
    return [f32(c0), f32(c1), f32(c2)]


def cross_bits(ab, bb):
    """cross over 32-bit input patterns, returning three 32-bit result patterns."""
    a = [frombits(u) for u in ab]
    b = [frombits(u) for u in bb]
    return [bits(c) for c in cross(a, b)]


def scale(s, v):
    """fp32 scalar-vector product s * [v0, v1, v2], each component one fp32
    multiply — the datapath the barycentric weighting (u = dot * inv_det, …)
    uses. `s` and the `v` elements are fp32 values; returns three fp32 values."""
    s = f32(s)
    return [f32(s * f32(v[0])), f32(s * f32(v[1])), f32(s * f32(v[2]))]


def scale_bits(sb, vb):
    """scale over 32-bit input patterns (scalar sb, vector vb), returning three
    32-bit result patterns."""
    s = frombits(sb)
    v = [frombits(u) for u in vb]
    return [bits(c) for c in scale(s, v)]


def recip(x):
    """fp32 reciprocal 1/x — the Moller-Trumbore inv_det step (inv_det = 1/det),
    a single correctly-rounded fp32 divide of the constant 1.0 by x. `x` is an
    fp32 value; returns the fp32 result."""
    return f32(f32(1.0) / f32(x))


def recip_bits(xb):
    """recip over a 32-bit input pattern, returning the 32-bit result pattern."""
    return bits(recip(frombits(xb)))


def normalize(v):
    """fp32 vector normalize v / ||v|| — the ray-direction conditioning step, in
    the exact datapath order the hardware uses:
        d   = dot3(v, v)      (fp32 fixed-order sum of squares)
        len = sqrt(d)         (correctly-rounded fp32 sqrt)
        inv = 1 / len         (correctly-rounded fp32 reciprocal)
        c_i = inv * v_i       (fp32 scale)
    Each step is a correctly-rounded fp32 op (numpy float32 == the HapiCore /
    SobekCore primitives). `v` elements are fp32 values; returns three fp32
    values."""
    d = dot3(v, v)
    length = f32(np.sqrt(f32(d)))
    inv = recip(length)
    return scale(inv, v)


def normalize_bits(vb):
    """normalize over 32-bit input patterns, returning three 32-bit patterns."""
    v = [frombits(u) for u in vb]
    return [bits(c) for c in normalize(v)]


def reflect(d, n):
    """fp32 specular reflection r = d - 2*(d.n)*n of incident vector d about a
    (unit) normal n, in the fixed datapath order:
        k     = dot3(d, n)      (fp32 fixed-order dot product)
        two_k = 2 * k           (fp32 multiply by exact 2.0)
        s     = scale(two_k, n) (fp32 scalar-vector product)
        r_i   = d_i - s_i       (fp32 subtract, exact negation)
    Each step is a correctly-rounded fp32 op. `d`, `n` elements are fp32 values;
    returns three fp32 values."""
    k = dot3(d, n)
    two_k = f32(f32(2.0) * f32(k))
    s = scale(two_k, n)
    return [f32(f32(d[i]) - f32(s[i])) for i in range(3)]


def reflect_bits(db, nb):
    """reflect over 32-bit input patterns (d, n), returning three 32-bit patterns."""
    d = [frombits(u) for u in db]
    n = [frombits(u) for u in nb]
    return [bits(c) for c in reflect(d, n)]


def ray_point(o, t, d):
    """fp32 ray parametric point p = o + t*d — evaluate the position at distance t
    along a ray, the single most-used ray operation (e.g. the hit point once the
    Moller-Trumbore t is known). Fixed datapath order:
        s_i = t * d_i     (fp32 scale)
        p_i = o_i + s_i   (fp32 add)
    Each step correctly-rounded fp32. `o`, `d` elements and `t` are fp32 values;
    returns three fp32 values."""
    s = scale(t, d)
    return [f32(f32(o[i]) + f32(s[i])) for i in range(3)]


def ray_point_bits(ob, tb, db):
    """ray_point over 32-bit patterns (origin ob, scalar tb, dir db) -> 3 patterns."""
    o = [frombits(u) for u in ob]
    d = [frombits(u) for u in db]
    return [bits(c) for c in ray_point(o, frombits(tb), d)]


def lerp(a, b, t):
    """fp32 linear interpolation r = a + t*(b - a) — blend two 3-vectors (e.g.
    interpolate a shading normal or attribute across a triangle). Fixed datapath
    order:
        e_i = b_i - a_i    (fp32 subtract, exact negation)
        s_i = t * e_i      (fp32 scale)
        r_i = a_i + s_i    (fp32 add)
    Each step correctly-rounded fp32. `a`, `b` elements and `t` are fp32 values;
    returns three fp32 values. Note t=0 -> a exactly; t=1 gives a + (b-a), the
    fp32-rounded value (the standard lerp trade-off), not necessarily b."""
    e = [f32(f32(b[i]) - f32(a[i])) for i in range(3)]
    s = scale(t, e)
    return [f32(f32(a[i]) + f32(s[i])) for i in range(3)]


def lerp_bits(ab, bb, tb):
    """lerp over 32-bit input patterns (a, b, scalar t) -> three 32-bit patterns."""
    a = [frombits(u) for u in ab]
    b = [frombits(u) for u in bb]
    return [bits(c) for c in lerp(a, b, frombits(tb))]
