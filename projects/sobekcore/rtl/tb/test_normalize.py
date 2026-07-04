"""cocotb testbench for SobekCore sobek_normalize — fp32 vector normalize
v / ||v||, bit-exact vs the fp32 golden sobek_fp32.normalize (combinational)."""
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
    got = [int(dut.c0.value), int(dut.c1.value), int(dut.c2.value)]
    exp = g.normalize_bits(vb)
    assert got == exp, f"normalize({v}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_normalize(dut):
    # directed cases
    await check(dut, [1.0, 0.0, 0.0])           # already unit -> unchanged
    await check(dut, [3.0, 4.0, 0.0])           # 3-4-5 -> (0.6, 0.8, 0)
    await check(dut, [1.0, 1.0, 1.0])           # 1/sqrt(3) each
    await check(dut, [-2.0, 0.0, 0.0])          # negative axis
    await check(dut, [0.0, 0.0, 5.0])           # single component

    rng = random.Random(0x40412E)

    # random normal-range non-degenerate vectors
    for _ in range(4000):
        v = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        if v[0] == 0.0 and v[1] == 0.0 and v[2] == 0.0:
            v[0] = 1.0
        await check(dut, v)

    # random wide-dynamic-range (exercise sqrt/div rounding, over/underflow of ||v||)
    for _ in range(4000):
        v = [rng.uniform(-1, 1) * 10 ** rng.randint(-10, 10) for _ in range(3)]
        if v[0] == 0.0 and v[1] == 0.0 and v[2] == 0.0:
            v[0] = 1.0
        await check(dut, v)

    dut._log.info("sobek_normalize verified bit-exact vs golden "
                  "sobek_fp32.normalize (8005 vectors)")
