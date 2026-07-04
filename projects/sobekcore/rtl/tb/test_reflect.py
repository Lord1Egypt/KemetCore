"""cocotb testbench for SobekCore sobek_reflect — fp32 specular reflection
r = d - 2*(d.n)*n, bit-exact vs the fp32 golden sobek_fp32.reflect."""
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


async def check(dut, d, n):
    db = [fbits(x) for x in d]
    nb = [fbits(x) for x in n]
    dut.d0.value, dut.d1.value, dut.d2.value = db
    dut.n0.value, dut.n1.value, dut.n2.value = nb
    await Timer(1, units="ns")
    got = [int(dut.r0.value), int(dut.r1.value), int(dut.r2.value)]
    exp = g.reflect_bits(db, nb)
    assert got == exp, f"reflect({d},{n}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_reflect(dut):
    # directed cases
    await check(dut, [1.0, -1.0, 0.0], [0.0, 1.0, 0.0])   # bounce off floor -> (1,1,0)
    await check(dut, [0.0, -1.0, 0.0], [0.0, 1.0, 0.0])   # head-on -> (0,1,0)
    await check(dut, [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])    # grazing (perp normal) -> unchanged
    await check(dut, [2.0, 3.0, -4.0], [0.0, 0.0, 1.0])   # reflect z
    await check(dut, [1.0, 1.0, 1.0], [1.0, 0.0, 0.0])    # reflect x

    rng = random.Random(0xEFEC7)

    # random normal-range
    for _ in range(3000):
        d = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        n = [rng.uniform(-1, 1) for _ in range(3)]
        await check(dut, d, n)

    # random wide-dynamic-range (rounding / cancellation / overflow)
    for _ in range(3000):
        d = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        n = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        await check(dut, d, n)

    dut._log.info("sobek_reflect verified bit-exact vs golden sobek_fp32.reflect "
                  "(6005 vectors)")
