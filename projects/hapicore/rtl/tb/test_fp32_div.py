"""cocotb testbench for hapi_fp32_div — bit-exact vs correctly-rounded golden fp_div.

Drives 32-bit operand pairs and checks y against golden.fp_div(...,'fp32'), which
rounds the exact rational a/b once. An independent in-TB oracle (nearest fp32 of
the exact rational) cross-checks the golden. NaN compared by class; sign of zero
IS checked.
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


async def check(dut, ab, bb):
    dut.a.value = ab
    dut.b.value = bb
    await Timer(1, units="ns")
    got = int(dut.y.value)

    af, bf = bits_to_f(ab), bits_to_f(bb)
    res = golden.fp_div(af, bf, "fp32")
    if isinstance(res, float) and res != res:
        assert is_nan_bits(got), f"{ab:08x}/{bb:08x}: got {got:08x}, expected NaN"
        return
    exp = f_to_bits(res)
    # independent oracle: golden must be the nearest fp32 of the exact rational
    if all(np.isfinite([af, bf])) and bf != 0.0 and af != 0.0:
        ex = Fraction(af) / Fraction(bf)
        if ex != 0 and np.isfinite(res):
            d = abs(Fraction(res) - ex)
            lo = float(np.nextafter(np.float32(res), np.float32(-np.inf)))
            hi = float(np.nextafter(np.float32(res), np.float32(np.inf)))
            if np.isfinite(lo):
                assert abs(Fraction(lo) - ex) >= d, f"golden not nearest(lo) for {af}/{bf}"
            if np.isfinite(hi):
                assert abs(Fraction(hi) - ex) >= d, f"golden not nearest(hi) for {af}/{bf}"
    assert got == exp, (
        f"{ab:08x}/{bb:08x}: got {got:08x} expected {exp:08x} ({af} / {bf} = {res})")


CORNERS = [
    0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x40000000, 0xC0000000,
    0x3F000000, 0x3FC00000, 0x7F800000, 0xFF800000, 0x7FC00000, 0x00000001,
    0x80000001, 0x007FFFFF, 0x00800000, 0x7F7FFFFF, 0xFF7FFFFF, 0x40490FDB,
    0x3EAAAAAB, 0x4B000000, 0x33800000,
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"fp32 div: {n} directed corner divisions verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xD1F032)
    n = 40000
    for _ in range(n):
        await check(dut, rng.getrandbits(32), rng.getrandbits(32))
    dut._log.info(f"fp32 div: {n} random divisions verified bit-exact")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    """Subnormal dividends/divisors (need input normalisation) + over/underflow."""
    pool = [0x00000001, 0x00000002, 0x00400000, 0x007FFFFF, 0x00800000,
            0x01000000, 0x3F800000, 0xBF800000, 0x40000000, 0x7F7FFFFF,
            0x7F000000, 0x00000010, 0x12345, 0x7E800000]
    n = 0
    for a in pool:
        for b in pool:
            await check(dut, a, b)
            await check(dut, a ^ 0x80000000, b)
            n += 2
    dut._log.info(f"fp32 div: {n} subnormal/overflow edge divisions verified")


@cocotb.test()
async def test_near_powers(dut):
    """a/b near a binade boundary stresses the q in (0.5,2) MSB selection + RNE."""
    rng = random.Random(0x9011E5)
    n = 0
    for _ in range(15000):
        b = rng.getrandbits(32)
        eb = (b >> 23) & 0xFF
        if eb in (0x00, 0xFF):
            continue
        # a = b * (1 +/- tiny) so the quotient sits right around 1.0
        a = (b & 0xFF800000) | (rng.getrandbits(23))
        a = (a + rng.randint(-3, 3)) & 0xFFFFFFFF
        await check(dut, a, b)
        n += 1
    dut._log.info(f"fp32 div: {n} near-unity-quotient divisions verified")
