"""cocotb testbench for SobekCore sobek_lerp — fp32 linear interpolation
r = a + t*(b-a), bit-exact vs the fp32 golden sobek_fp32.lerp."""
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


async def check(dut, a, b, t):
    ab = [fbits(x) for x in a]
    bb = [fbits(x) for x in b]
    tb = fbits(t)
    dut.a0.value, dut.a1.value, dut.a2.value = ab
    dut.b0.value, dut.b1.value, dut.b2.value = bb
    dut.t.value = tb
    await Timer(1, units="ns")
    got = [int(dut.r0.value), int(dut.r1.value), int(dut.r2.value)]
    exp = g.lerp_bits(ab, bb, tb)
    assert got == exp, f"lerp({a},{b},{t}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_lerp(dut):
    # directed cases
    await check(dut, [0.0, 0.0, 0.0], [1.0, 2.0, 3.0], 0.0)   # t=0 -> a
    await check(dut, [0.0, 0.0, 0.0], [2.0, 4.0, 6.0], 0.5)   # midpoint
    await check(dut, [1.0, 1.0, 1.0], [3.0, 3.0, 3.0], 1.0)   # t=1 -> b
    await check(dut, [-1.0, 2.0, 0.0], [1.0, -2.0, 4.0], 0.25)
    await check(dut, [5.0, 5.0, 5.0], [5.0, 5.0, 5.0], 0.7)   # a==b -> a

    rng = random.Random(0x1E4901)

    # random normal-range, t in [0,1] and a bit beyond (extrapolation)
    for _ in range(3000):
        a = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        b = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        t = rng.uniform(-0.5, 1.5)
        await check(dut, a, b, t)

    # random wide-dynamic-range (rounding / cancellation / overflow)
    for _ in range(3000):
        a = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        b = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        t = rng.uniform(-1, 1) * 10 ** rng.randint(-4, 4)
        await check(dut, a, b, t)

    dut._log.info("sobek_lerp verified bit-exact vs golden sobek_fp32.lerp "
                  "(6005 vectors)")
