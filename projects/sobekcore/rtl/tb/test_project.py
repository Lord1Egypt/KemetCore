"""cocotb testbench for SobekCore sobek_project — fp32 projection of a onto b,
bit-exact vs the fp32 golden sobek_fp32.project (combinational, no clock)."""
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
    got = [int(dut.c0.value), int(dut.c1.value), int(dut.c2.value)]
    exp = g.project_bits(ab, bb)
    assert got == exp, f"project({a},{b}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_project(dut):
    await check(dut, [2.0, 2.0, 0.0], [1.0, 0.0, 0.0])   # -> (2,0,0)
    await check(dut, [1.0, 6.0, 9.0], [0.0, 3.0, 0.0])   # -> (0,6,0)
    await check(dut, [1.0, 1.0, 1.0], [1.0, 1.0, 1.0])   # a==b -> b
    await check(dut, [3.0, 0.0, 4.0], [0.0, 0.0, 1.0])   # -> (0,0,4)
    await check(dut, [-2.0, 4.0, 0.0], [1.0, 1.0, 0.0])  # ab=2,bb=2,s=1 -> (1,1,0)

    rng = random.Random(0x9203EC)
    for _ in range(4000):
        a = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        b = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        if b[0] == 0.0 and b[1] == 0.0 and b[2] == 0.0:
            b[0] = 1.0
        await check(dut, a, b)
    for _ in range(4000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        if b[0] == 0.0 and b[1] == 0.0 and b[2] == 0.0:
            b[0] = 1.0
        await check(dut, a, b)

    dut._log.info("sobek_project verified bit-exact vs golden sobek_fp32.project "
                  "(8005 vectors)")
