"""HapiCore golden reference — IEEE-754 floating-point arithmetic.

The golden model IS the specification. fp16 and fp32 use numpy's IEEE-754
dtypes directly (these are correctly-rounded hardware semantics); bf16 is
implemented as round-to-nearest-even truncation of fp32. fma is *genuinely*
single-rounded: the exact real value a*b+c is formed with rational
(fractions.Fraction) arithmetic — so no precision is lost — and rounded once
into the target format. This matches a real fused hardware unit (and the RTL
hapi_fp32_fma), unlike the naive `cast(a*b+c)` which double-rounds.

Supported here (Phase 0): add, sub, mul, fma, cmp, classify, cast for
fp16 / bf16 / fp32. div/sqrt and fp64 arrive with the RTL (Phase 2).
"""
import math
import struct
from fractions import Fraction

import numpy as np

_DT = {"fp16": np.float16, "fp32": np.float32}
FORMATS = ("fp16", "bf16", "fp32")

# Per-format IEEE parameters: (significand bits incl. implicit, min normal
# unbiased exponent, max biased exponent value used to detect overflow->Inf).
#   value = significand(1.f) * 2**e,  emin <= e <= emax  for normals;
#   smallest subnormal = 2**(emin - (p-1)).
_FMT = {
    #            p   emin  emax
    "fp16": (11, -14, 15),
    "bf16": (8, -126, 127),
    "fp32": (24, -126, 127),
}


def fp32_to_fp16(u):
    """Narrow an fp32 bit-pattern u to a 16-bit fp16 (IEEE half), round-to-nearest-
    even. numpy float16 is the correctly-rounded oracle; a NaN becomes a canonical
    quiet fp16 NaN (sign | 0x7E00). Matches the hapi_fp32_to_fp16 RTL."""
    f = np.frombuffer(struct.pack("<I", u & 0xFFFFFFFF), np.float32)[0]
    if np.isnan(f):
        return ((u >> 16) & 0x8000) | 0x7E00
    return int(np.frombuffer(np.float16(f).tobytes(), np.uint16)[0])


def bf16_to_fp32(h):
    """Widen a 16-bit bf16 bit-pattern to fp32 (exact): append 16 zero mantissa
    bits. Matches the hapi_bf16_to_fp32 RTL."""
    return (h & 0xFFFF) << 16


def fp16_to_fp32(h):
    """Widen a 16-bit fp16 (IEEE half) bit-pattern to fp32, returning the 32-bit
    value. The upcast is exact; numpy is the oracle for finite values, while
    Inf/NaN use the exact payload-preserving widening (mantissa = m16 << 13) to
    match the hapi_fp16_to_fp32 RTL."""
    h &= 0xFFFF
    sign, e16, m16 = (h >> 15) & 1, (h >> 10) & 0x1F, h & 0x3FF
    if e16 == 0x1F:
        return (sign << 31) | (0xFF << 23) | (m16 << 13)
    f16 = np.frombuffer(struct.pack("<H", h), np.float16)[0]
    return int(np.frombuffer(struct.pack("<f", np.float32(f16)), np.uint32)[0])



def fp32_sgnj(a, b, op):
    """RISC-V fp32 sign-injection: a's magnitude with a sign from b.
    op: 0 fsgnj (b.sign), 1 fsgnjn (~b.sign), 2 fsgnjx (a.sign^b.sign). Exact."""
    a &= 0xFFFFFFFF
    b &= 0xFFFFFFFF
    if op == 0:
        sgn = (b >> 31) & 1
    elif op == 1:
        sgn = ((b >> 31) & 1) ^ 1
    else:
        sgn = ((a >> 31) & 1) ^ ((b >> 31) & 1)
    return (sgn << 31) | (a & 0x7FFFFFFF)


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



def fp32_to_bf16(u):
    """Round an fp32 bit-pattern u to a 16-bit bf16 (round-to-nearest-even),
    returning the 16-bit value. Finite values use the RNE-at-bit-16 formula
    (carries propagate into the exponent, so an overflow becomes Inf); Inf passes
    through; a NaN is preserved as a canonical quiet bf16 NaN. Matches the
    hapi_fp32_to_bf16 RTL."""
    u &= 0xFFFFFFFF
    if (u & 0x7F800000) == 0x7F800000 and (u & 0x007FFFFF) != 0:   # NaN
        return ((u >> 16) & 0x8000) | 0x7FC0
    return ((u + 0x7FFF + ((u >> 16) & 1)) >> 16) & 0xFFFF


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


def _round_frac(frac, sign, fmt):
    """Round an exact non-negative rational magnitude to `fmt`, applying `sign`.

    Round-to-nearest, ties-to-even. Handles normals, subnormals (gradual
    underflow) and overflow -> Inf. `frac` is a fractions.Fraction >= 0.
    """
    p, emin, emax = _FMT[fmt]
    if frac == 0:
        return -0.0 if sign else 0.0
    # leading binade exponent e: 2**e <= frac < 2**(e+1)
    e = frac.numerator.bit_length() - frac.denominator.bit_length()
    if Fraction(2) ** e > frac:
        e -= 1
    elif Fraction(2) ** (e + 1) <= frac:
        e += 1
    # quantum exponent: ULP = 2**qe.  Clamp to the subnormal grid at emin.
    qe = max(e - (p - 1), emin - (p - 1))
    scaled = frac / (Fraction(2) ** qe)          # exact; ideal integer mantissa
    num, den = scaled.numerator, scaled.denominator
    n = num // den
    rem2 = 2 * (num - n * den)
    if rem2 > den or (rem2 == den and (n & 1)):  # round half to even
        n += 1
    value = n * (Fraction(2) ** qe)
    if value >= Fraction(2) ** (emax + 1):       # overflow -> Inf
        out = math.inf
    else:
        out = float(value)                       # exact: n*2**qe is representable
    return -out if sign else out


def fp_fma(a, b, c, fmt="fp32"):
    """Fused multiply-add a*b+c with a single final rounding (exact intermediate)."""
    a, b, c = cast(a, fmt), cast(b, fmt), cast(c, fmt)
    # Special operands first (NaN/Inf), mirroring real fused hardware.
    if math.isnan(a) or math.isnan(b) or math.isnan(c):
        return float("nan")
    prod = a * b                                  # inf*finite=inf, inf*0 below
    if math.isnan(prod):                          # 0 * Inf -> invalid -> NaN
        return float("nan")
    if math.isinf(prod) or math.isinf(c):
        s = prod + c                              # Inf + (-Inf) -> NaN
        return cast(s, fmt)
    # Both prod and c finite: form a*b+c EXACTLY, then round exactly once.
    exact = Fraction(a) * Fraction(b) + Fraction(c)
    if exact == 0:
        # IEEE: a sum that is exactly zero is +0 except -0 + -0 -> -0.
        ab_neg = math.copysign(1.0, a) * math.copysign(1.0, b) < 0
        c_neg = math.copysign(1.0, c) < 0
        both_zero = (a == 0.0 or b == 0.0) and c == 0.0
        return -0.0 if (both_zero and ab_neg and c_neg) else 0.0
    return _round_frac(abs(exact), exact < 0, fmt)


def fp_div(a, b, fmt="fp32"):
    """Correctly-rounded division a/b (exact rational intermediate, one rounding)."""
    a, b = cast(a, fmt), cast(b, fmt)
    sign = (math.copysign(1.0, a) < 0) ^ (math.copysign(1.0, b) < 0)
    if math.isnan(a) or math.isnan(b):
        return float("nan")
    if math.isinf(a) and math.isinf(b):
        return float("nan")                       # Inf/Inf -> invalid
    if b == 0.0:
        if a == 0.0:
            return float("nan")                   # 0/0 -> invalid
        return -math.inf if sign else math.inf    # x/0 -> signed Inf
    if math.isinf(a):
        return -math.inf if sign else math.inf
    if math.isinf(b) or a == 0.0:
        return -0.0 if sign else 0.0              # finite/Inf or 0/finite -> signed 0
    return _round_frac(abs(Fraction(a) / Fraction(b)), sign, fmt)


def _round_sqrt_int(s):
    """Round sqrt(s) to the nearest integer, ties-to-even. s is a Fraction >= 0."""
    p, q = s.numerator, s.denominator
    n0 = math.isqrt(p * q) // q                   # floor(sqrt(s))
    lhs = 4 * p                                    # compare s vs (n0+0.5)**2
    rhs = (2 * n0 + 1) ** 2 * q
    if lhs > rhs:
        return n0 + 1
    if lhs < rhs:
        return n0
    return n0 if (n0 & 1) == 0 else n0 + 1         # exact tie -> even


def fp_sqrt(x, fmt="fp32"):
    """Correctly-rounded square root (exact integer-sqrt intermediate)."""
    x = cast(x, fmt)
    if math.isnan(x):
        return float("nan")
    if x == 0.0:
        return x                                   # +0 -> +0, -0 -> -0
    if x < 0.0:
        return float("nan")                        # sqrt of negative (incl -Inf)
    if math.isinf(x):
        return math.inf
    p, _emin, _emax = _FMT[fmt]
    fx = Fraction(x)
    e = fx.numerator.bit_length() - fx.denominator.bit_length() - 1
    if Fraction(2) ** e > fx:
        e -= 1
    elif Fraction(2) ** (e + 1) <= fx:
        e += 1
    eres = e >> 1                                  # floor(e/2)
    qe = eres - (p - 1)                            # tentative quantum exponent
    for _ in range(3):                             # settle the binade (round-up carry)
        n = _round_sqrt_int(fx / (Fraction(2) ** (2 * qe)))
        if n >= (1 << p):
            qe += 1
        elif n < (1 << (p - 1)):
            qe -= 1
        else:
            break
    return float(n * (Fraction(2) ** qe))          # always a normal, exactly representable


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
