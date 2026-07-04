"""cocotb testbench for SobekCore sobek_reject — fp32 rejection a - proj_b(a),
bit-exact vs the fp32 golden sobek_fp32.reject (combinational, no clock)."""
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
    got = [int(dut.r0.value), int(dut.r1.value), int(dut.r2.value)]
    exp = g.reject_bits(ab, bb)
    assert got == exp, f"reject({a},{b}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_reject(dut):
    await check(dut, [2.0, 2.0, 0.0], [1.0, 0.0, 0.0])   # -> (0,2,0)
    await check(dut, [3.0, 3.0, 3.0], [1.0, 1.0, 1.0])   # parallel -> ~0
    await check(dut, [1.0, 6.0, 9.0], [0.0, 3.0, 0.0])   # -> (1,0,9)
    await check(dut, [3.0, 0.0, 4.0], [0.0, 0.0, 1.0])   # -> (3,0,0)
    await check(dut, [-2.0, 4.0, 1.0], [1.0, 1.0, 0.0])  # remove (1,1,0)

    rng = random.Random(0x9EEC70)
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

    dut._log.info("sobek_reject verified bit-exact vs golden sobek_fp32.reject "
                  "(8005 vectors)")
