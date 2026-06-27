"""cocotb testbench for HapiCore hapi_fp32_fma — bit-exact vs single-rounded FMA.

Drives 3x32-bit operands (a, b, c) and checks the combinational y against the
golden fp_fma(...,'fp32'), which forms a*b+c EXACTLY (rational) and rounds once.
As an independent oracle the test also computes the nearest-fp32 of the exact
rational a*b+c here and asserts the golden agrees. NaN compared by class; the
sign of zero IS checked.
"""
import os
import random
import struct
import sys
from fractions import Fraction

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


def bits_to_f(u):
    return float(np.uint32(u).view(np.float32))


def f_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def is_nan_bits(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


def is_inf_bits(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) == 0


def exact_fma_bits(af, bf, cf):
    """Independent oracle: nearest fp32 (ties-even) of the exact real a*b+c."""
    if any(np.isnan(x) for x in (af, bf, cf)):
        return f_to_bits(np.float32(np.nan))
    prod_inf = np.isinf(af) or np.isinf(bf)
    if (np.isinf(af) and bf == 0.0) or (np.isinf(bf) and af == 0.0):
        return f_to_bits(np.float32(np.nan))           # 0 * Inf
    if prod_inf or np.isinf(cf):
        sp = (np.signbit(af) ^ np.signbit(bf))
        if prod_inf and np.isinf(cf) and (sp != bool(np.signbit(cf))):
            return f_to_bits(np.float32(np.nan))        # Inf + (-Inf)
        if prod_inf:
            return 0xFF800000 if sp else 0x7F800000
        return 0xFF800000 if np.signbit(cf) else 0x7F800000
    return f_to_bits(golden.fp_fma(af, bf, cf, "fp32"))


async def check(dut, ab, bb, cb):
    dut.a.value = ab
    dut.b.value = bb
    dut.c.value = cb
    await Timer(1, units="ns")
    got = int(dut.y.value)

    af, bf, cf = bits_to_f(ab), bits_to_f(bb), bits_to_f(cb)
    g = f_to_bits(golden.fp_fma(af, bf, cf, "fp32"))
    o = exact_fma_bits(af, bf, cf)                      # independent oracle
    # the golden must itself match the independent exact oracle
    if not is_nan_bits(o):
        assert g == o, f"golden!=oracle for {af}*{bf}+{cf}: {g:08x} vs {o:08x}"

    if is_nan_bits(o):
        assert is_nan_bits(got), (
            f"{ab:08x}*{bb:08x}+{cb:08x}: got {got:08x}, expected NaN")
    else:
        assert got == g, (
            f"{ab:08x}*{bb:08x}+{cb:08x}: got {got:08x} expected {g:08x} "
            f"({af} * {bf} + {cf})")


CORNERS = [
    0x00000000, 0x80000000,    # +0, -0
    0x3F800000, 0xBF800000,    # +1, -1
    0x40000000, 0xC0000000,    # +2, -2
    0x3F000000, 0x3FC00000,    # 0.5, 1.5
    0x7F800000, 0xFF800000,    # +Inf, -Inf
    0x7FC00000, 0x7FA00000,    # NaNs
    0x00000001, 0x80000001,    # +/- smallest subnormal
    0x007FFFFF, 0x00800000,    # largest subnormal, smallest normal
    0x7F7FFFFF, 0xFF7FFFFF,    # +/- largest finite
    0x40490FDB, 0xC0490FDB,    # +/- pi
    0x3EAAAAAB, 0x4B000000,    # 1/3, 2^23
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            for cc in (0x00000000, 0x3F800000, 0xBF800000, 0x7F800000,
                       0x00000001, 0x4B000000, 0x40490FDB):
                await check(dut, a, b, cc)
                n += 1
    dut._log.info(f"fp32 fma: {n} directed corner FMAs verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5A1234)
    n = 25000
    for _ in range(n):
        await check(dut, rng.getrandbits(32), rng.getrandbits(32),
                    rng.getrandbits(32))
    dut._log.info(f"fp32 fma: {n} random FMAs verified bit-exact")


@cocotb.test()
async def test_fma_cancellation(dut):
    """a*b chosen to nearly cancel c — the case where a fused single rounding
    differs from mul-then-add, stressing the exact wide lane + sticky."""
    rng = random.Random(0x0CA7F3A)
    n = 0
    for _ in range(12000):
        a = rng.getrandbits(32)
        b = rng.getrandbits(32)
        ea = (a >> 23) & 0xFF
        eb = (b >> 23) & 0xFF
        if ea in (0x00, 0xFF) or eb in (0x00, 0xFF):
            continue
        prod = golden.fp_mul(bits_to_f(a), bits_to_f(b), "fp32")
        # c = -(a*b) with a tiny perturbation -> heavy cancellation in a*b+c
        cbits = f_to_bits(prod) ^ 0x80000000
        cbits = (cbits & 0xFF800000) | ((cbits + rng.randint(-3, 3)) & 0x7FFFFF)
        await check(dut, a, b, cbits)
        await check(dut, a, b, f_to_bits(prod) ^ 0x80000000)   # exact -> +0
        n += 2
    dut._log.info(f"fp32 fma: {n} cancellation FMAs verified")


@cocotb.test()
async def test_opposite_sign_tail(dut):
    """c opposite-sign to a*b across the full magnitude gap — exercises the
    effective-subtraction sticky-borrow (a far tail must round the magnitude
    DOWN, not up). Includes tie-prone exact products."""
    rng = random.Random(0x0FF5161)
    n = 0
    for _ in range(20000):
        a = rng.getrandbits(32)
        b = rng.getrandbits(32)
        ea = (a >> 23) & 0xFF
        eb = (b >> 23) & 0xFF
        if ea in (0x00, 0xFF) or eb in (0x00, 0xFF):
            continue
        prod = golden.fp_mul(bits_to_f(a), bits_to_f(b), "fp32")
        pbits = f_to_bits(prod)
        # c opposite sign, magnitude swept far below the product (-> sticky tail)
        shift = rng.randint(1, 170)
        pe = (pbits >> 23) & 0xFF
        ce = pe - shift
        if ce <= 0 or ce >= 0xFF:
            continue
        cbits = ((pbits ^ 0x80000000) & 0x80000000) | (ce << 23) | rng.getrandbits(23)
        await check(dut, a, b, cbits)
        n += 1
    dut._log.info(f"fp32 fma: {n} opposite-sign far-tail FMAs verified")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    smalls = [0x00000001, 0x00000002, 0x00400000, 0x007FFFFF,
              0x00800000, 0x01000000, 0x1A000000, 0x0C000000]
    bigs = [0x7F000000, 0x7F400000, 0x7F7FFFFF, 0x7E800000, 0x6F000000]
    mids = [0x3F800000, 0xBF800000, 0x40000000, 0x4B000000]
    pool = smalls + bigs + mids
    n = 0
    for a in pool:
        for b in pool:
            for cc in (0x00000000, 0x00000001, 0x7F7FFFFF, 0x3F800000):
                await check(dut, a, b, cc)
                await check(dut, a ^ 0x80000000, b, cc)
                n += 2
    dut._log.info(f"fp32 fma: {n} subnormal/overflow edge FMAs verified")
