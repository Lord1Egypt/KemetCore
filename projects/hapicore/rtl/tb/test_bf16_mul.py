"""cocotb testbench for HapiCore hapi_bf16_mul — bit-exact vs the Python golden.

Drives 16-bit bf16 operand pairs and checks the combinational product against
golden.fp_mul(a, b, "bf16") (round-to-nearest-even of the exact product). NaN
results are compared by class, not payload (payload bits are not architectural).
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
    """bf16 bit pattern (16b) -> Python float (via fp32)."""
    return float(np.uint32(bits << 16).view(np.float32))


def f_to_bits(f):
    """A bf16-valued float -> its 16-bit bf16 pattern (top half of fp32)."""
    u = int(np.float32(f).view(np.uint32))
    return (u >> 16) & 0xFFFF


def is_nan_bits(bits):
    return ((bits >> 7) & 0xFF) == 0xFF and (bits & 0x7F) != 0


async def check(dut, abits, bbits):
    dut.a.value = abits
    dut.b.value = bbits
    await Timer(1, units="ns")
    got = int(dut.y.value)

    exp_f = golden.fp_mul(bits_to_f(abits), bits_to_f(bbits), "bf16")
    exp = f_to_bits(exp_f)

    if is_nan_bits(exp):
        assert is_nan_bits(got), (
            f"{abits:04x}*{bbits:04x}: got {got:04x}, expected a NaN")
    else:
        assert got == exp, (
            f"{abits:04x}*{bbits:04x}: got {got:04x} != exp {exp:04x} "
            f"({bits_to_f(abits)} * {bits_to_f(bbits)} = {exp_f})")


# A spread of architecturally interesting bf16 patterns.
CORNERS = [
    0x0000, 0x8000,            # +0, -0
    0x3F80, 0xBF80,            # +1, -1
    0x4000, 0x3F00,            # +2, +0.5
    0x3FC0, 0x4040,            # 1.5, 3.0
    0x7F80, 0xFF80,            # +Inf, -Inf
    0x7FC0, 0x7FA0, 0xFFC0,    # NaNs
    0x0001, 0x8001, 0x007F,    # smallest/largest subnormals
    0x0080, 0x7F7F, 0xFF7F,    # smallest normal, largest finite
    0x4049, 0x402D, 0x3EAA,    # ~pi, ~e, ~1/3
    0x5D5D, 0x1F1F,            # large / small normals (overflow/underflow bait)
]


@cocotb.test()
async def test_corners(dut):
    n = 0
    for a in CORNERS:
        for b in CORNERS:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"bf16 mul: {n} directed corner products verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0FFEE)
    n = 6000
    for _ in range(n):
        a = rng.getrandbits(16)
        b = rng.getrandbits(16)
        await check(dut, a, b)
    dut._log.info(f"bf16 mul: {n} random products verified bit-exact")


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    """Target the underflow/overflow rounding edges explicitly."""
    smalls = [0x0001, 0x0002, 0x0040, 0x007F, 0x0080, 0x0100, 0x0200]
    bigs = [0x7F00, 0x7F40, 0x7F7F, 0x7E00, 0x6000, 0x5000]
    pool = smalls + bigs + [0x3F80, 0x4000, 0x3F00]
    n = 0
    for a in pool:
        for b in pool:
            await check(dut, a, b)
            await check(dut, a ^ 0x8000, b)  # flip a sign too
            n += 2
    dut._log.info(f"bf16 mul: {n} subnormal/overflow edge products verified")
