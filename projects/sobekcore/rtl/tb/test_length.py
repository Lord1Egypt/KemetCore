"""cocotb testbench for SobekCore sobek_length — fp32 vector length ||v||,
bit-exact vs the fp32 golden sobek_fp32.length (combinational, no clock)."""
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


async def check(dut, v):
    vb = [fbits(x) for x in v]
    dut.v0.value, dut.v1.value, dut.v2.value = vb
    await Timer(1, units="ns")
    got = int(dut.len.value)
    exp = g.length_bits(vb)
    assert got == exp, f"length({v}): got {hex(got)} exp {hex(exp)}"


@cocotb.test()
async def test_length(dut):
    # directed cases
    await check(dut, [3.0, 4.0, 0.0])       # 3-4-5 -> 5
    await check(dut, [1.0, 0.0, 0.0])       # unit -> 1
    await check(dut, [0.0, 0.0, 0.0])       # zero -> 0
    await check(dut, [2.0, 3.0, 6.0])       # -> 7 (2^2+3^2+6^2=49)
    await check(dut, [-1.0, -2.0, -2.0])    # negatives -> 3

    rng = random.Random(0x1E4076)

    # random normal-range
    for _ in range(4000):
        v = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        await check(dut, v)

    # random wide-dynamic-range (sqrt rounding, over/underflow of the sum of squares)
    for _ in range(4000):
        v = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        await check(dut, v)

    dut._log.info("sobek_length verified bit-exact vs golden sobek_fp32.length "
                  "(8005 vectors)")
