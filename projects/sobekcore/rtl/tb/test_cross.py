"""cocotb testbench for SobekCore sobek_cross — fp32 3-D cross product,
bit-exact vs the fp32 golden sobek_fp32.cross (combinational, no clock)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import sobek_fp32 as g  # noqa: E402


def fbits(x):
    """python float -> fp32 32-bit pattern."""
    return struct.unpack("<I", struct.pack("<f", x))[0]


async def check(dut, a, b):
    ab = [fbits(x) for x in a]
    bb = [fbits(x) for x in b]
    dut.a0.value, dut.a1.value, dut.a2.value = ab
    dut.b0.value, dut.b1.value, dut.b2.value = bb
    await Timer(1, units="ns")
    got = [int(dut.c0.value), int(dut.c1.value), int(dut.c2.value)]
    exp = g.cross_bits(ab, bb)
    assert got == exp, f"cross({a},{b}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_cross(dut):
    # directed cases
    await check(dut, [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])         # x cross y = z
    await check(dut, [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])         # y cross z = x
    await check(dut, [1.0, 2.0, 3.0], [4.0, 5.0, 6.0])         # (-3, 6, -3)
    await check(dut, [2.0, 3.0, 4.0], [2.0, 3.0, 4.0])         # parallel -> 0
    await check(dut, [-1.0, -2.0, -3.0], [3.0, 2.0, 1.0])      # negatives

    rng = random.Random(0xC3055)

    # random normal-range vectors
    for _ in range(3000):
        a = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        b = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        await check(dut, a, b)

    # random wide-dynamic-range (exercise rounding / cancellation / overflow)
    for _ in range(3000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        await check(dut, a, b)

    dut._log.info("sobek_cross verified bit-exact vs golden sobek_fp32.cross "
                  "(6005 vectors)")
