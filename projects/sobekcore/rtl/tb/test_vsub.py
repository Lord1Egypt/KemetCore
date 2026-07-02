"""cocotb testbench for SobekCore sobek_vsub — fp32 3-vector subtract,
bit-exact vs the fp32 golden sobek_fp32.vsub (combinational, no clock)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import sobek_fp32 as g  # noqa: E402


def fbits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


async def check(dut, a, b):
    ab = [fbits(x) for x in a]
    bb = [fbits(x) for x in b]
    dut.a0.value, dut.a1.value, dut.a2.value = ab
    dut.b0.value, dut.b1.value, dut.b2.value = bb
    await Timer(1, units="ns")
    got = [int(dut.d0.value), int(dut.d1.value), int(dut.d2.value)]
    exp = g.vsub_bits(ab, bb)
    assert got == exp, f"vsub({a},{b}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_vsub(dut):
    # directed
    await check(dut, [1.0, 2.0, 3.0], [0.5, 0.5, 0.5])        # (0.5,1.5,2.5)
    await check(dut, [1.0, 1.0, 1.0], [1.0, 1.0, 1.0])        # zero
    await check(dut, [0.0, 0.0, 0.0], [1.0, -2.0, 3.0])       # -b
    await check(dut, [1e30, -1e30, 1.0], [-1e30, 1e30, 1.0])  # large mag

    rng = random.Random(0x5B00B)

    for _ in range(3000):
        a = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        b = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        await check(dut, a, b)

    for _ in range(3000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        await check(dut, a, b)

    dut._log.info("sobek_vsub verified bit-exact vs golden sobek_fp32.vsub "
                  "(6004 vectors)")
