import math

import numpy as np
import pytest

import hapi_fpu as g
from hapi_fpu_model import FpuPipeline, LATENCY


def test_add_matches_numpy():
    rng = np.random.default_rng(0)
    for _ in range(2000):
        a, b = rng.standard_normal(2).astype(np.float32) * 10
        assert g.fp_add(a, b, "fp32") == float(np.float32(np.float32(a) + np.float32(b)))
        a16, b16 = np.float16(a), np.float16(b)
        assert g.fp_add(a16, b16, "fp16") == float(np.float16(a16 + b16))


def test_bf16_round_cases():
    # 1.0 is exactly representable
    assert g.round_bf16(1.0) == 1.0
    # bf16 has 7 mantissa bits; 1 + 2^-8 rounds to nearest even -> 1.0
    assert g.round_bf16(1.0 + 2 ** -8) == 1.0
    # 1 + 2^-7 is exactly representable
    assert g.round_bf16(1.0 + 2 ** -7) == 1.0 + 2 ** -7
    # non-finite passes through
    assert math.isinf(g.round_bf16(float("inf")))
    assert math.isnan(g.round_bf16(float("nan")))


def test_mul_commutative():
    rng = np.random.default_rng(1)
    for fmt in g.FORMATS:
        for _ in range(500):
            a, b = rng.standard_normal(2) * 5
            assert g.fp_mul(a, b, fmt) == g.fp_mul(b, a, fmt)


def test_fma_more_accurate():
    # a*b is exact in fp64 but loses bits when forced through fp32 twice.
    a = np.float32(1 + 2 ** -12)
    b = np.float32(1 + 2 ** -12)
    c = np.float32(-1.0)
    true = (float(a) * float(b)) + float(c)
    fused = g.fp_fma(a, b, c, "fp32")
    separate = g.fp_add(g.fp_mul(a, b, "fp32"), c, "fp32")
    assert abs(fused - true) <= abs(separate - true)


def test_fma_single_rounded():
    """fp_fma is exactly the nearest fp32 to the real value a*b+c (one rounding)."""
    from fractions import Fraction
    rng = np.random.default_rng(7)
    for _ in range(4000):
        a, b, c = (rng.standard_normal(3).astype(np.float32) * 10).tolist()
        a, b, c = float(np.float32(a)), float(np.float32(b)), float(np.float32(c))
        got = g.fp_fma(a, b, c, "fp32")
        exact = Fraction(a) * Fraction(b) + Fraction(c)
        if exact == 0:
            assert got == 0.0
            continue
        # no representable fp32 is strictly closer to the exact value than `got`
        d = abs(Fraction(got) - exact)
        lo = float(np.nextafter(np.float32(got), np.float32(-np.inf)))
        hi = float(np.nextafter(np.float32(got), np.float32(np.inf)))
        assert abs(Fraction(lo) - exact) >= d
        assert abs(Fraction(hi) - exact) >= d


def test_div_single_rounded():
    """fp_div is exactly the nearest fp32 to the real value a/b (one rounding)."""
    from fractions import Fraction
    rng = np.random.default_rng(11)
    for _ in range(4000):
        a, b = (rng.standard_normal(2).astype(np.float32) * 10).tolist()
        a, b = float(np.float32(a)), float(np.float32(b))
        if b == 0.0:
            continue
        got = g.fp_div(a, b, "fp32")
        exact = Fraction(a) / Fraction(b)
        if exact == 0:
            assert got == 0.0
            continue
        if not math.isfinite(got):
            continue
        d = abs(Fraction(got) - exact)
        lo = float(np.nextafter(np.float32(got), np.float32(-np.inf)))
        hi = float(np.nextafter(np.float32(got), np.float32(np.inf)))
        assert abs(Fraction(lo) - exact) >= d
        assert abs(Fraction(hi) - exact) >= d


def test_div_specials():
    assert g.fp_div(1.0, 0.0, "fp32") == math.inf            # x/0 -> +Inf
    assert g.fp_div(-1.0, 0.0, "fp32") == -math.inf
    assert math.isnan(g.fp_div(0.0, 0.0, "fp32"))            # 0/0 -> NaN
    assert math.isnan(g.fp_div(math.inf, math.inf, "fp32"))  # Inf/Inf -> NaN
    assert g.fp_div(1.0, math.inf, "fp32") == 0.0            # finite/Inf -> 0
    assert g.fp_div(7.0, 2.0, "fp32") == 3.5
    assert math.copysign(1.0, g.fp_div(-1.0, math.inf, "fp32")) < 0  # -0


def test_sqrt_single_rounded():
    """fp_sqrt is exactly the nearest fp32 to the real sqrt(x) (correctly rounded)."""
    from fractions import Fraction
    rng = np.random.default_rng(13)
    for _ in range(4000):
        x = float(abs(np.float32(rng.standard_normal() * 1e3)))
        if x == 0.0:
            continue
        r = g.fp_sqrt(x, "fp32")
        ex = Fraction(x)
        rr = Fraction(r)
        lo = float(np.nextafter(np.float32(r), np.float32(-np.inf)))
        hi = float(np.nextafter(np.float32(r), np.float32(np.inf)))
        if math.isfinite(lo):
            mid = (Fraction(lo) + rr) / 2
            assert mid * mid <= ex                 # sqrt(x) >= midpoint to lower neighbor
        if math.isfinite(hi):
            mid = (rr + Fraction(hi)) / 2
            assert ex <= mid * mid                 # sqrt(x) <= midpoint to upper neighbor


def test_sqrt_specials():
    assert g.fp_sqrt(4.0, "fp32") == 2.0
    assert g.fp_sqrt(9.0, "fp32") == 3.0
    assert g.fp_sqrt(0.0, "fp32") == 0.0
    assert math.copysign(1.0, g.fp_sqrt(-0.0, "fp32")) < 0      # sqrt(-0) = -0
    assert math.isnan(g.fp_sqrt(-2.0, "fp32"))                  # sqrt(<0) = NaN
    assert math.isnan(g.fp_sqrt(-math.inf, "fp32"))
    assert g.fp_sqrt(math.inf, "fp32") == math.inf
    assert g.fp_sqrt(2.0 ** -149, "fp32") > 0                   # subnormal in -> normal out


def test_fma_specials():
    assert math.isnan(g.fp_fma(0.0, math.inf, 1.0, "fp32"))      # 0*Inf -> NaN
    assert math.isnan(g.fp_fma(math.inf, 1.0, -math.inf, "fp32"))  # Inf-Inf -> NaN
    assert math.isinf(g.fp_fma(3.0e38, 3.0e38, 0.0, "fp32"))      # overflow -> Inf
    assert g.fp_fma(2.0, 3.0, 1.0, "fp32") == 7.0
    # exact subnormal product survives single rounding (no flush)
    assert g.fp_fma(2.0 ** -74, 2.0 ** -75, 0.0, "fp32") == 2.0 ** -149


def test_specials():
    inf, nan = float("inf"), float("nan")
    assert math.isnan(g.fp_add(inf, -inf, "fp32"))
    assert math.isnan(g.fp_mul(0.0, inf, "fp32"))
    assert math.isinf(g.fp_add(inf, 1.0, "fp32"))
    assert g.fp_cmp(nan, 1.0, "fp32") is None
    assert g.classify(nan) == "nan"
    assert g.classify(0.0) == "zero"
    assert g.classify(1.0) == "normal"
    # signed zero compares equal
    assert g.fp_cmp(-0.0, 0.0, "fp32") == 0


def test_classify_subnormal():
    assert g.classify(2.0 ** -140, "fp32") == "subnormal"
    assert g.classify(2.0 ** -20, "fp16") == "subnormal"


def test_pymodel_latency():
    p = FpuPipeline("fp32")
    r = p.add(1.0, 2.0)
    assert r == g.fp_add(1.0, 2.0, "fp32")
    assert p.cycles == LATENCY["add"]
    p.mul(2.0, 3.0)
    p.fma(1.0, 2.0, 3.0)
    assert p.cycles == LATENCY["add"] + LATENCY["mul"] + LATENCY["fma"]


def test_pymodel_matches_golden():
    rng = np.random.default_rng(2)
    p = FpuPipeline("bf16")
    for _ in range(300):
        a, b, c = rng.standard_normal(3) * 4
        assert p.add(a, b) == g.fp_add(a, b, "bf16")
        assert p.fma(a, b, c) == g.fp_fma(a, b, c, "bf16")


def test_fp32_to_bf16():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    # exact (low 16 bits zero) passes through unchanged
    assert g.fp32_to_bf16(f2b(1.0)) == (f2b(1.0) >> 16)
    assert g.fp32_to_bf16(f2b(-2.0)) == (f2b(-2.0) >> 16)
    # round-half-to-even at bit 16
    assert g.fp32_to_bf16(0x3F808000) == 0x3F80          # tie -> even (down)
    assert g.fp32_to_bf16(0x3F818000) == 0x3F82          # tie -> even (up)
    assert g.fp32_to_bf16(0x3F808001) == 0x3F81          # above tie -> up
    # Inf passes through; max finite overflows to Inf
    assert g.fp32_to_bf16(0x7F800000) == 0x7F80
    assert g.fp32_to_bf16(0x7F7FFFFF) == 0x7F80
    # NaN preserved as a quiet bf16 NaN (not collapsed to Inf)
    assert g.fp32_to_bf16(0x7F800001) == 0x7FC0
    assert g.fp32_to_bf16(0xFFABCDEF) == 0xFFC0
    # vs round_bf16 top-16 for finite values
    for x in [0.0, 1.5, -3.25, 1e20, 1e-20, np.pi]:
        rb = f2b(g.round_bf16(x)) >> 16
        assert g.fp32_to_bf16(f2b(x)) == rb


def test_fp32_to_fp16():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    # known fp16 encodings (hand-verified, independent of numpy round path)
    assert g.fp32_to_fp16(f2b(1.0)) == 0x3C00
    assert g.fp32_to_fp16(f2b(-2.0)) == 0xC000
    assert g.fp32_to_fp16(f2b(0.0)) == 0x0000
    assert g.fp32_to_fp16(f2b(-0.0)) == 0x8000
    assert g.fp32_to_fp16(0x7F800000) == 0x7C00          # +Inf
    assert g.fp32_to_fp16(0xFF800000) == 0xFC00          # -Inf
    assert g.fp32_to_fp16(f2b(65504.0)) == 0x7BFF        # fp16 max finite
    assert g.fp32_to_fp16(f2b(70000.0)) == 0x7C00        # overflow -> Inf
    assert g.fp32_to_fp16(f2b(6e-8)) == 0x0001           # smallest subnormal region
    assert g.fp32_to_fp16(f2b(1e-10)) == 0x0000          # underflow -> 0
    # NaN -> quiet fp16 NaN (not Inf)
    assert g.fp32_to_fp16(0x7F800001) == 0x7E00
    # vs numpy float16 over a sweep of finite values
    for _ in range(500):
        x = np.float32(np.random.uniform(-100000, 100000))
        u = f2b(x)
        assert g.fp32_to_fp16(u) == int(np.frombuffer(np.float16(x).tobytes(), np.uint16)[0])


def test_fp16_to_fp32():
    import struct

    def b2f32(u):
        return struct.unpack("<f", struct.pack("<I", u))[0]

    # known widenings
    assert g.fp16_to_fp32(0x3C00) == 0x3F800000          # 1.0
    assert g.fp16_to_fp32(0xC000) == 0xC0000000          # -2.0
    assert g.fp16_to_fp32(0x0000) == 0x00000000          # +0
    assert g.fp16_to_fp32(0x8000) == 0x80000000          # -0
    assert g.fp16_to_fp32(0x7C00) == 0x7F800000          # +Inf
    assert g.fp16_to_fp32(0xFC00) == 0xFF800000          # -Inf
    assert g.fp16_to_fp32(0x0001) == 0x33800000          # smallest subnormal 2^-24
    assert g.fp16_to_fp32(0x03FF) == 0x387FC000          # largest subnormal
    assert g.fp16_to_fp32(0x7BFF) == 0x477FE000          # max finite 65504
    # round-trip: fp16 -> fp32 -> fp16 is identity for all 65536 patterns
    for h in range(0x10000):
        u = g.fp16_to_fp32(h)
        e16 = (h >> 10) & 0x1F
        if e16 == 0x1F and (h & 0x3FF):       # NaN: payload preserved, still NaN
            assert (u & 0x7F800000) == 0x7F800000 and (u & 0x007FFFFF) != 0
        else:
            assert g.fp32_to_fp16(u) == h


def test_bf16_to_fp32():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    # bf16 = top 16 bits of fp32; widening appends 16 zeros
    assert g.bf16_to_fp32(0x3F80) == 0x3F800000          # 1.0
    assert g.bf16_to_fp32(0xC000) == 0xC0000000          # -2.0
    assert g.bf16_to_fp32(0x7F80) == 0x7F800000          # +Inf
    assert g.bf16_to_fp32(0x0000) == 0x00000000          # +0
    # round-trip: fp32_to_bf16(bf16_to_fp32(h)) == h for all bf16 patterns
    for h in range(0x10000):
        u = g.bf16_to_fp32(h)
        assert u == (h << 16)
        e = (h >> 7) & 0xFF
        if not (e == 0xFF and (h & 0x7F)):     # skip NaN (round narrows to quiet)
            assert g.fp32_to_bf16(u) == h


def test_fp32_sgnj():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    pos1, neg1, pos2, neg2 = f2b(1.0), f2b(-1.0), f2b(2.0), f2b(-2.0)
    # fsgnj: take b's sign
    assert g.fp32_sgnj(pos1, neg2, 0) == neg1          # |1| with - -> -1
    assert g.fp32_sgnj(neg1, pos2, 0) == pos1          # |-1| with + -> 1
    # fsgnjn: ~b sign
    assert g.fp32_sgnj(pos1, pos2, 1) == neg1
    # fsgnjx: a.sign ^ b.sign (fabs via x,x ; fneg via n,x)
    assert g.fp32_sgnj(neg1, neg1, 2) == pos1          # -1 ^ -1 -> +
    assert g.fp32_sgnj(neg1, pos1, 2) == neg1          # - ^ + -> -
    # magnitude (incl NaN payload) preserved
    nan = 0x7FABCDEF
    assert g.fp32_sgnj(nan, 0x80000000, 0) == (nan | 0x80000000)
    assert g.fp32_sgnj(nan, 0x00000000, 0) == (nan & 0x7FFFFFFF)


def test_fp32_minmax():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    p1, n1, p2 = f2b(1.0), f2b(-1.0), f2b(2.0)
    assert g.fp32_minmax(p1, p2, 0) == p1          # min(1,2)=1
    assert g.fp32_minmax(p1, p2, 1) == p2          # max(1,2)=2
    assert g.fp32_minmax(n1, p1, 0) == n1          # min(-1,1)=-1
    # -0 < +0
    pz, nz = 0x00000000, 0x80000000
    assert g.fp32_minmax(pz, nz, 0) == nz          # min(+0,-0) = -0
    assert g.fp32_minmax(pz, nz, 1) == pz          # max(+0,-0) = +0
    # one NaN -> other operand; both NaN -> canonical qNaN
    nan = 0x7FABCDEF
    assert g.fp32_minmax(nan, p2, 0) == p2
    assert g.fp32_minmax(p2, nan, 1) == p2
    assert g.fp32_minmax(nan, 0x7F800001, 0) == 0x7FC00000
    # Inf handling
    inf, ninf = 0x7F800000, 0xFF800000
    assert g.fp32_minmax(inf, p2, 0) == p2
    assert g.fp32_minmax(ninf, p2, 0) == ninf


def test_fp32_cmp():
    import struct

    def f2b(x):
        return struct.unpack("<I", struct.pack("<f", np.float32(x)))[0]

    p1, n1, p2 = f2b(1.0), f2b(-1.0), f2b(2.0)
    assert g.fp32_cmp(p1, p1, 0) == 1          # feq 1==1
    assert g.fp32_cmp(p1, p2, 0) == 0
    assert g.fp32_cmp(p1, p2, 1) == 1          # flt 1<2
    assert g.fp32_cmp(p2, p1, 1) == 0
    assert g.fp32_cmp(p1, p1, 2) == 1          # fle 1<=1
    assert g.fp32_cmp(n1, p1, 1) == 1          # flt -1<1
    # +0 == -0
    pz, nz = 0x00000000, 0x80000000
    assert g.fp32_cmp(pz, nz, 0) == 1
    assert g.fp32_cmp(pz, nz, 1) == 0          # not strictly less
    assert g.fp32_cmp(pz, nz, 2) == 1
    # NaN -> all false
    nan = 0x7FABCDEF
    for op in range(3):
        assert g.fp32_cmp(nan, p1, op) == 0
        assert g.fp32_cmp(p1, nan, op) == 0


def test_fp32_class():
    assert g.fp32_class(0xFF800000) == (1 << 0)    # -Inf
    assert g.fp32_class(0xBF800000) == (1 << 1)    # -normal
    assert g.fp32_class(0x80000001) == (1 << 2)    # -subnormal
    assert g.fp32_class(0x80000000) == (1 << 3)    # -0
    assert g.fp32_class(0x00000000) == (1 << 4)    # +0
    assert g.fp32_class(0x00000001) == (1 << 5)    # +subnormal
    assert g.fp32_class(0x3F800000) == (1 << 6)    # +normal
    assert g.fp32_class(0x7F800000) == (1 << 7)    # +Inf
    assert g.fp32_class(0x7F800001) == (1 << 8)    # sNaN (mantissa MSB clear)
    assert g.fp32_class(0x7FC00000) == (1 << 9)    # qNaN (mantissa MSB set)
    # exactly one bit set for every input
    import random
    for _ in range(300):
        assert bin(g.fp32_class(random.getrandbits(32))).count("1") == 1


def test_int_to_fp32():
    import struct

    def b2f(u):
        return float(np.frombuffer(struct.pack("<I", u), np.float32)[0])

    assert b2f(g.int_to_fp32(0, 1)) == 0.0
    assert b2f(g.int_to_fp32(1, 1)) == 1.0
    assert b2f(g.int_to_fp32(0xFFFFFFFF, 1)) == -1.0          # signed -1
    assert b2f(g.int_to_fp32(0xFFFFFFFF, 0)) == 4294967296.0  # unsigned, RNE -> 2^32
    assert b2f(g.int_to_fp32(0x80000000, 1)) == -2147483648.0
    assert b2f(g.int_to_fp32(0x7FFFFFFF, 1)) == 2147483648.0   # rounds up to 2^31
    # cross-check vs numpy over random
    for _ in range(2000):
        x = np.random.randint(0, 1 << 32, dtype=np.uint64) & 0xFFFFFFFF
        for s in (0, 1):
            iv = np.int32(np.uint32(x)) if s else np.uint32(x)
            ref = int(np.frombuffer(np.float32(iv).tobytes(), np.uint32)[0])
            assert g.int_to_fp32(int(x), s) == ref
