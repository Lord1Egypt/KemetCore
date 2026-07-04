"""cocotb testbench for SobekCore sobek_scale — fp32 scalar-vector product,
bit-exact vs the fp32 golden sobek_fp32.scale (combinational, no clock)."""
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


async def check(dut, s, v):
    sb = fbits(s)
    vb = [fbits(x) for x in v]
    dut.s.value = sb
    dut.v0.value, dut.v1.value, dut.v2.value = vb
    await Timer(1, units="ns")
    got = [int(dut.c0.value), int(dut.c1.value), int(dut.c2.value)]
    exp = g.scale_bits(sb, vb)
    assert got == exp, f"scale({s},{v}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_scale(dut):
    # directed cases
    await check(dut, 1.0, [1.0, 2.0, 3.0])           # identity scale
    await check(dut, 0.0, [1.0, -2.0, 3.0])          # zero scalar
    await check(dut, -1.0, [1.5, -2.5, 4.0])         # negate
    await check(dut, 2.0, [0.5, 0.25, 0.125])        # exact powers of two
    await check(dut, 3.0, [1.0, 1.0, 1.0])           # rounding exercise later

    rng = random.Random(0x5CA1E)

    # random normal-range
    for _ in range(3000):
        s = rng.uniform(-1e3, 1e3)
        v = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        await check(dut, s, v)

    # random wide-dynamic-range (rounding / overflow / underflow)
    for _ in range(3000):
        s = rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20)
        v = [rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20) for _ in range(3)]
        await check(dut, s, v)

    dut._log.info("sobek_scale verified bit-exact vs golden sobek_fp32.scale "
                  "(6005 vectors)")
