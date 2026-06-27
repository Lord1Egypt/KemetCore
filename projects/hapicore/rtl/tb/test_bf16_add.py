"""cocotb testbench for HapiCore hapi_bf16_add — bit-exact vs the Python golden.

Drives 16-bit bf16 operand pairs and checks the combinational sum against
golden.fp_add(a, b, "bf16") (round-to-nearest-even of the exact sum). NaN results
are compared by class, not payload. Signed zero IS checked (sign bit matters).
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
    return float(np.uint32(bits << 16).view(np.float32))


def f_to_bits(f):
    u = int(np.float32(f).view(np.uint32))
    return (u >> 16) & 0xFFFF


def is_nan_bits(bits):
    return ((bits >> 7) & 0xFF) == 0xFF and (bits & 0x7F) != 0


async def check(dut, abits, bbits):
    dut.a.value = abits
    dut.b.value = bbits
    await Timer(1, units="ns")
    got = int(dut.y.value)

    exp_f = golden.fp_add(bits_to_f(abits), bits_to_f(bbits), "bf16")
    exp = f_to_bits(exp_f)

    if is_nan_bits(exp):
        assert is_nan_bits(got), (
            f"{abits:04x}+{bbits:04x}: got {got:04x}, expected a NaN")
    else:
        # full 16-bit match, including the sign of zero
        assert got == exp, (
            f"{abits:04x}+{bbits:04x}: got {got:04x} != exp {exp:04x} "
            f"({bits_to_f(abits)} + {bits_to_f(bbits)} = {exp_f})")


CORNERS = [
    0x0000, 0x8000,            # +0, -0
    0x3F80, 0xBF80,            # +1, -1
    0x4000, 0xC000, 0x3F00,    # +2, -2, +0.5
    0x3FC0, 0x4040, 0xC040,    # 1.5, 3.0, -3.0
    0x7F80, 0xFF80,            # +Inf, -Inf
    0x7FC0, 0x7FA0,            # NaNs
    0x0001, 0x8001, 0x007F,    # subnormals
    0x0080, 0x8080, 0x7F7F,    # smallest normal (+/-), largest finite
    0x4049, 0xC049, 0x3EAA,    # pi, -pi, 1/3
    0x4900, 0x4880,            # values that cancel to small diffs
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"bf16 add: {n} directed corner sums verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xABCDEF)
    n = 6000
    for _ in range(n):
        a = rng.getrandbits(16)
        b = rng.getrandbits(16)
        await check(dut, a, b)
    dut._log.info(f"bf16 add: {n} random sums verified bit-exact")


@cocotb.test()
async def test_cancellation(dut):
    """Near-equal magnitudes (catastrophic cancellation) + sign-of-zero rules."""
    rng = random.Random(0x13579B)
    n = 0
    for _ in range(3000):
        a = rng.getrandbits(16)
        # b close to -a in magnitude: same exp, mantissa +/- a small delta
        e = (a >> 7) & 0xFF
        if e in (0x00, 0xFF):
            continue
        m = (a + rng.randint(-3, 3)) & 0x7F
        b = ((a ^ 0x8000) & 0xFF80) | m       # opposite sign, nearby mantissa
        await check(dut, a, b)
        await check(dut, a, a ^ 0x8000)        # exact x + (-x) = +0
        n += 2
    dut._log.info(f"bf16 add: {n} cancellation/signed-zero sums verified")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    smalls = [0x0001, 0x0002, 0x0040, 0x007F, 0x0080, 0x0100]
    bigs = [0x7F00, 0x7F40, 0x7F7F, 0x7E80, 0x7E00]
    pool = smalls + bigs + [0x3F80, 0xBF80, 0x4000]
    n = 0
    for a in pool:
        for b in pool:
            await check(dut, a, b)
            await check(dut, a ^ 0x8000, b)
            n += 2
    dut._log.info(f"bf16 add: {n} subnormal/overflow edge sums verified")
