"""cocotb testbench for SobekCore sobek_ray_point — fp32 ray parametric point
p = o + t*d, bit-exact vs the fp32 golden sobek_fp32.ray_point."""
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


async def check(dut, o, t, d):
    ob = [fbits(x) for x in o]
    db = [fbits(x) for x in d]
    tb = fbits(t)
    dut.o0.value, dut.o1.value, dut.o2.value = ob
    dut.t.value = tb
    dut.d0.value, dut.d1.value, dut.d2.value = db
    await Timer(1, units="ns")
    got = [int(dut.p0.value), int(dut.p1.value), int(dut.p2.value)]
    exp = g.ray_point_bits(ob, tb, db)
    assert got == exp, f"ray_point({o},{t},{d}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_raypoint(dut):
    # directed cases
    await check(dut, [0.0, 0.0, 0.0], 1.0, [1.0, 2.0, 3.0])   # t=1 from origin
    await check(dut, [1.0, 1.0, 1.0], 0.0, [9.0, 9.0, 9.0])   # t=0 -> origin
    await check(dut, [0.0, 0.0, 5.0], 2.0, [0.0, 0.0, -1.0])  # down toward plane
    await check(dut, [1.0, 2.0, 3.0], -1.0, [1.0, 1.0, 1.0])  # negative t
    await check(dut, [0.25, 0.25, 1.0], 1.0, [0.0, 0.0, -1.0])  # Moller-Trumbore hit

    rng = random.Random(0x2A9901)

    # random normal-range
    for _ in range(3000):
        o = [rng.uniform(-1e3, 1e3) for _ in range(3)]
        t = rng.uniform(-1e2, 1e2)
        d = [rng.uniform(-1e2, 1e2) for _ in range(3)]
        await check(dut, o, t, d)

    # random wide-dynamic-range (rounding / cancellation / overflow)
    for _ in range(3000):
        o = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        t = rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8)
        d = [rng.uniform(-1, 1) * 10 ** rng.randint(-15, 15) for _ in range(3)]
        await check(dut, o, t, d)

    dut._log.info("sobek_ray_point verified bit-exact vs golden "
                  "sobek_fp32.ray_point (6005 vectors)")
