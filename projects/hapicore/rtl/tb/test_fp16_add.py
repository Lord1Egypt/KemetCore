"""cocotb testbench for HapiCore hapi_fp16_add — bit-exact vs the Python golden.

Drives 16-bit fp16 (IEEE half) operand pairs and checks the combinational sum
against golden.fp_add(a, b, "fp16") (numpy float16, round-to-nearest-even). NaN
results are compared by class, not payload. Exercises cancellation, alignment,
subnormals and overflow.
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


def bits_to_f(bits):
    return float(np.uint16(bits).view(np.float16))


def f_to_bits(f):
    return int(np.float16(f).view(np.uint16)) & 0xFFFF


def is_nan_bits(bits):
    return ((bits >> 10) & 0x1F) == 0x1F and (bits & 0x3FF) != 0


async def check(dut, abits, bbits):
    dut.a.value = abits
    dut.b.value = bbits
    await Timer(1, units="ns")
    got = int(dut.y.value)

    with np.errstate(over="ignore", invalid="ignore"):
        exp_f = golden.fp_add(bits_to_f(abits), bits_to_f(bbits), "fp16")
    exp = f_to_bits(exp_f)

    if is_nan_bits(exp):
        assert is_nan_bits(got), f"{abits:04x}+{bbits:04x}: got {got:04x}, expected a NaN"
    else:
        assert got == exp, (
            f"{abits:04x}+{bbits:04x}: got {got:04x} != exp {exp:04x} "
            f"({bits_to_f(abits)} + {bits_to_f(bbits)} = {exp_f})")


CORNERS = [
    0x0000, 0x8000,            # +0, -0
    0x3C00, 0xBC00,            # +1, -1
    0x4000, 0x3800,            # +2, +0.5
    0x3E00, 0x4200,            # 1.5, 3.0
    0x7C00, 0xFC00,            # +Inf, -Inf
    0x7E00, 0x7D00, 0xFE00,    # NaNs
    0x0001, 0x8001, 0x03FF,    # smallest/largest subnormals
    0x0400, 0x7BFF, 0xFBFF,    # smallest normal, largest finite
    0x4248, 0x4170, 0x3555,    # ~pi, ~e, ~1/3
    0x7800, 0x0C00,            # large / small normals
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"fp16 add: {n} directed corner sums verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xADD16)
    n = 8000
    for _ in range(n):
        await check(dut, rng.getrandbits(16), rng.getrandbits(16))
    dut._log.info(f"fp16 add: {n} random sums verified bit-exact")


@cocotb.test()
async def test_cancellation(dut):
    """Near-equal magnitudes with opposite signs — the catastrophic-cancellation path."""
    rng = random.Random(0xCA4CE1)
    n = 0
    for _ in range(3000):
        a = rng.getrandbits(16)
        # b close to -a: same/neighbouring exponent, opposite sign, perturbed mantissa
        delta = rng.randint(-4, 4) & 0x3FF
        b = (a ^ 0x8000) & 0xFFFF
        b = (b & 0xFC00) | (((b & 0x3FF) + delta) & 0x3FF)
        await check(dut, a, b)
        n += 1
    dut._log.info(f"fp16 add: {n} cancellation cases verified bit-exact")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    smalls = [0x0001, 0x0002, 0x0010, 0x0200, 0x03FF, 0x0400, 0x0401, 0x0800]
    bigs = [0x7800, 0x7A00, 0x7BFF, 0x7B00, 0x6000, 0x5000]
    pool = smalls + bigs + [0x3C00, 0x4000, 0x3800]
    n = 0
    for a in pool:
        for b in pool:
            await check(dut, a, b)
            await check(dut, a, b ^ 0x8000)  # flip b sign -> effective subtract
            n += 2
    dut._log.info(f"fp16 add: {n} subnormal/overflow edge sums verified")
