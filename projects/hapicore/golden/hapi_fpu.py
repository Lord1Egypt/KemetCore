"""HapiCore golden reference — IEEE-754 floating-point arithmetic.

The golden model IS the specification. fp16 and fp32 use numpy's IEEE-754
dtypes directly (these are correctly-rounded hardware semantics); bf16 is
implemented as round-to-nearest-even truncation of fp32. fma uses an fp64
intermediate so it is single-rounded relative to the target format.

Supported here (Phase 0): add, sub, mul, fma, cmp, classify, cast for
fp16 / bf16 / fp32. div/sqrt and fp64 arrive with the RTL (Phase 2).
"""
import math

import numpy as np

_DT = {"fp16": np.float16, "fp32": np.float32}
FORMATS = ("fp16", "bf16", "fp32")


def round_bf16(x):
    """Round a real value to the nearest bf16 (8 exp / 7 mantissa), ties-to-even.

    Returns a Python float holding the (fp32-exact) bf16 value.
    """
    a = np.float32(x)
    if not np.isfinite(a):
        return float(a)
    u = int(a.view(np.uint32))
    lsb = (u >> 16) & 1
    u = (u + 0x7FFF + lsb) & 0xFFFFFFFF      # round-to-nearest-even at bit 16
    u &= 0xFFFF0000                          # truncate low 16 mantissa bits
    return float(np.uint32(u).view(np.float32))


def cast(x, fmt="fp32"):
    """Round a value into the given format, returned as a Python float."""
    if fmt == "bf16":
        return round_bf16(x)
    return float(_DT[fmt](x))


def fp_add(a, b, fmt="fp32"):
    with np.errstate(invalid="ignore", over="ignore"):
        if fmt == "bf16":
            return round_bf16(round_bf16(a) + round_bf16(b))
        dt = _DT[fmt]
        return float(dt(dt(a) + dt(b)))


def fp_sub(a, b, fmt="fp32"):
    return fp_add(a, -cast(b, fmt) if not _is_nan(b) else b, fmt)


def fp_mul(a, b, fmt="fp32"):
    with np.errstate(invalid="ignore", over="ignore"):
        if fmt == "bf16":
            return round_bf16(round_bf16(a) * round_bf16(b))
        dt = _DT[fmt]
        return float(dt(dt(a) * dt(b)))


def fp_fma(a, b, c, fmt="fp32"):
    """Fused multiply-add a*b+c with a single final rounding (fp64 intermediate)."""
    a, b, c = cast(a, fmt), cast(b, fmt), cast(c, fmt)
    return cast((a * b) + c, fmt)


def fp_cmp(a, b, fmt="fp32"):
    """Return -1/0/1, or None if unordered (NaN operand)."""
    a, b = cast(a, fmt), cast(b, fmt)
    if math.isnan(a) or math.isnan(b):
        return None
    return -1 if a < b else (1 if a > b else 0)


def classify(x, fmt="fp32"):
    a = cast(x, fmt)
    if math.isnan(a):
        return "nan"
    if math.isinf(a):
        return "inf"
    if a == 0.0:
        return "zero"
    # subnormal: nonzero but below the format's smallest normal magnitude
    smallest_normal = {"fp16": 2.0 ** -14, "bf16": 2.0 ** -126, "fp32": 2.0 ** -126}[fmt]
    if abs(a) < smallest_normal:
        return "subnormal"
    return "normal"


def _is_nan(x):
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False
