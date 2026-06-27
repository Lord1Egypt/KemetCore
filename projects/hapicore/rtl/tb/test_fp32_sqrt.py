"""cocotb testbench for hapi_fp32_sqrt — bit-exact vs correctly-rounded golden fp_sqrt.

Drives a 32-bit operand and checks y against golden.fp_sqrt(...,'fp32'), which
rounds the exact real sqrt(x) once. An independent in-TB oracle verifies the golden
is the nearest fp32 (via exact rational midpoint-square comparisons). NaN compared
by class; sign of zero IS checked.
"""
import os
import random
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


async def check(dut, xb):
    dut.x.value = xb
    await Timer(1, units="ns")
    got = int(dut.y.value)

    xf = bits_to_f(xb)
    res = golden.fp_sqrt(xf, "fp32")
    if isinstance(res, float) and res != res:
        assert is_nan_bits(got), f"sqrt({xb:08x}): got {got:08x}, expected NaN"
        return
    exp = f_to_bits(res)
    # independent oracle: golden must be the nearest fp32 to the real sqrt(xf)
    if np.isfinite(xf) and xf > 0.0 and np.isfinite(res):
        ex = Fraction(xf)
        rr = Fraction(res)
        lo = float(np.nextafter(np.float32(res), np.float32(-np.inf)))
        hi = float(np.nextafter(np.float32(res), np.float32(np.inf)))
        if np.isfinite(lo):
            mid = (Fraction(lo) + rr) / 2
            assert mid * mid <= ex, f"golden not nearest(lo) for sqrt({xf})"
        if np.isfinite(hi):
            mid = (rr + Fraction(hi)) / 2
            assert ex <= mid * mid, f"golden not nearest(hi) for sqrt({xf})"
    assert got == exp, f"sqrt({xb:08x}): got {got:08x} expected {exp:08x} (sqrt({xf}) = {res})"


CORNERS = [
    0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x40000000, 0x40800000,
    0x41100000, 0x7F800000, 0xFF800000, 0x7FC00000, 0x00000001, 0x80000001,
    0x007FFFFF, 0x00800000, 0x7F7FFFFF, 0xFF7FFFFF, 0x40490FDB, 0x3F000000,
    0x4B000000, 0x33800000, 0x3E800000, 0x42C80000,
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        await check(dut, a)
        n += 1
    dut._log.info(f"fp32 sqrt: {n} directed corner roots verified bit-exact")


@cocotb.test()
async def test_perfect_squares(dut):
    """sqrt of exact squares n*n must be exactly n (no rounding)."""
    n = 0
    for k in range(1, 4000):
        v = float(k * k)
        await check(dut, f_to_bits(v))
        n += 1
    dut._log.info(f"fp32 sqrt: {n} perfect squares verified")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5023A7)
    n = 60000
    for _ in range(n):
        await check(dut, rng.getrandbits(32))
    dut._log.info(f"fp32 sqrt: {n} random roots verified bit-exact")


@cocotb.test()
async def test_subnormal_and_edges(dut):
    pool = [0x00000001, 0x00000002, 0x00000004, 0x00400000, 0x007FFFFF,
            0x00800000, 0x01000000, 0x00000010, 0x12345, 0x7F7FFFFF,
            0x7F000000, 0x3F800001, 0x3F7FFFFF, 0x00000003]
    n = 0
    for a in pool:
        await check(dut, a)
        n += 1
    # dense sweep just above/below 1.0 (quotient-of-binade boundary for sqrt)
    rng = random.Random(0x53B011)
    for _ in range(8000):
        await check(dut, 0x3F800000 + rng.randint(-2000, 2000))
        n += 1
    dut._log.info(f"fp32 sqrt: {n} subnormal/near-one roots verified")
