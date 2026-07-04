"""cocotb testbench for SobekCore sobek_distance — fp32 Euclidean distance
||a - b||, bit-exact vs the fp32 golden sobek_fp32.distance (combinational)."""
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
    got = int(dut.len.value)
    exp = g.distance_bits(ab, bb)
    assert got == exp, f"distance({a},{b}): got {hex(got)} exp {hex(exp)}"


@cocotb.test()
async def test_distance(dut):
    # directed cases
    await check(dut, [0.0, 0.0, 0.0], [3.0, 4.0, 0.0])    # -> 5
    await check(dut, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0])    # coincident -> 0
    await check(dut, [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0])   # -> 2
    await check(dut, [0.0, 0.0, 0.0], [2.0, 3.0, 6.0])    # -> 7
    await check(dut, [5.0, 5.0, 5.0], [5.0, 5.0, 2.0])    # -> 3

    rng = random.Random(0xD15CE)

    # random normal-range
    for _ in range(4000):
        a = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        b = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        await check(dut, a, b)

    # random wide-dynamic-range (subtract cancellation, sqrt rounding, over/underflow)
    for _ in range(4000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        await check(dut, a, b)

    dut._log.info("sobek_distance verified bit-exact vs golden "
                  "sobek_fp32.distance (8005 vectors)")
