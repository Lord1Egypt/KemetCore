"""cocotb testbench for SobekCore sobek_dot3 — fp32 3-element dot product,
bit-exact vs the fp32 golden sobek_fp32.dot3 (combinational, no clock)."""
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
    got = int(dut.y.value)
    exp = g.dot3_bits(ab, bb)
    assert got == exp, (
        f"dot3({a},{b}): got {got:#010x} exp {exp:#010x}"
    )


@cocotb.test()
async def test_dot3(dut):
    # directed cases
    await check(dut, [1.0, 2.0, 3.0], [4.0, 5.0, 6.0])          # 32.0
    await check(dut, [0.0, 0.0, 0.0], [1.0, 2.0, 3.0])          # 0.0
    await check(dut, [-1.0, 2.0, -3.0], [4.0, -5.0, 6.0])       # negatives
    await check(dut, [1e20, 1.0, -1e20], [1.0, 1.0, 1.0])       # catastrophic cancel
    await check(dut, [1e30, 1e30, 1e30], [1e30, 1e30, 1e30])    # overflow -> inf

    rng = random.Random(0x50BE7)

    # random normal-range vectors
    for _ in range(3000):
        a = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        b = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        await check(dut, a, b)

    # random wide-dynamic-range (exercise rounding / cancellation)
    for _ in range(3000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        await check(dut, a, b)

    dut._log.info("sobek_dot3 verified bit-exact vs golden sobek_fp32.dot3 "
                  "(6005 vectors)")
