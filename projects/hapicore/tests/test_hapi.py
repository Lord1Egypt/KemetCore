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
