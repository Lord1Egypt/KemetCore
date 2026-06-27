"""cocotb testbench for HapiCore hapi_fp32_mul — bit-exact vs IEEE-754 fp32.

Drives 32-bit operand pairs and checks the combinational product against numpy's
float32 multiply. NaN results compared by class; signed zero IS checked.
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


def bits_to_f(u):
    return np.uint32(u).view(np.float32)


def f_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def is_nan_bits(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def check(dut, ab, bb):
    dut.a.value = ab
    dut.b.value = bb
    await Timer(1, units="ns")
    got = int(dut.y.value)

    with np.errstate(invalid="ignore", over="ignore"):
        res = np.float32(bits_to_f(ab) * bits_to_f(bb))
    exp = f_to_bits(res)
    g = f_to_bits(golden.fp_mul(float(bits_to_f(ab)), float(bits_to_f(bb)), "fp32"))

    if is_nan_bits(exp):
        assert is_nan_bits(got), f"{ab:08x}*{bb:08x}: got {got:08x}, expected a NaN"
    else:
        assert got == exp == g, (
            f"{ab:08x}*{bb:08x}: got {got:08x} exp {exp:08x} golden {g:08x} "
            f"({bits_to_f(ab)} * {bits_to_f(bb)} = {res})")


CORNERS = [
    0x00000000, 0x80000000,    # +0, -0
    0x3F800000, 0xBF800000,    # +1, -1
    0x40000000, 0x3F000000,    # +2, +0.5
    0x3FC00000, 0x40400000,    # 1.5, 3.0
    0x7F800000, 0xFF800000,    # +Inf, -Inf
    0x7FC00000, 0x7FA00000,    # NaNs
    0x00000001, 0x80000001,    # +/- smallest subnormal
    0x007FFFFF, 0x00800000,    # largest subnormal, smallest normal
    0x7F7FFFFF, 0xFF7FFFFF,    # +/- largest finite
    0x40490FDB, 0x3EAAAAAB,    # pi, 1/3
    0x5D5E0000, 0x21000000,    # large / small (overflow/underflow bait)
    0x3F7FFFFF, 0x3F800001,    # just below / above 1.0
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"fp32 mul: {n} directed corner products verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0FFEE32)
    n = 40000
    for _ in range(n):
        await check(dut, rng.getrandbits(32), rng.getrandbits(32))
    dut._log.info(f"fp32 mul: {n} random products verified bit-exact")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    smalls = [0x00000001, 0x00000002, 0x00400000, 0x007FFFFF,
              0x00800000, 0x01000000, 0x02000000]
    bigs = [0x7F000000, 0x7F400000, 0x7F7FFFFF, 0x7E000000,
            0x6F000000, 0x60000000]
    pool = smalls + bigs + [0x3F800000, 0x40000000, 0x3F000000]
    n = 0
    for a in pool:
        for b in pool:
            await check(dut, a, b)
            await check(dut, a ^ 0x80000000, b)
            n += 2
    dut._log.info(f"fp32 mul: {n} subnormal/overflow edge products verified")
