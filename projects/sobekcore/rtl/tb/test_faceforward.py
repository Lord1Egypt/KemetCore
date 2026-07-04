"""cocotb testbench for SobekCore sobek_faceforward — orient a normal against a
ray, bit-exact vs the fp32 golden sobek_fp32.faceforward (combinational)."""
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


async def check(dut, n, d):
    nb = [fbits(x) for x in n]
    db = [fbits(x) for x in d]
    dut.n0.value, dut.n1.value, dut.n2.value = nb
    dut.d0.value, dut.d1.value, dut.d2.value = db
    await Timer(1, units="ns")
    got = [int(dut.r0.value), int(dut.r1.value), int(dut.r2.value)]
    exp = g.faceforward_bits(nb, db)
    assert got == exp, f"faceforward({n},{d}): got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_faceforward(dut):
    # directed cases
    await check(dut, [0.0, 1.0, 0.0], [0.0, -1.0, 0.0])   # ray hits front: k<0 -> keep
    await check(dut, [0.0, 1.0, 0.0], [0.0, 1.0, 0.0])    # ray behind: k>0 -> flip
    await check(dut, [0.0, 1.0, 0.0], [1.0, 0.0, 0.0])    # perpendicular: k==0 -> keep
    await check(dut, [1.0, 2.0, 3.0], [-1.0, -2.0, -3.0]) # k<0 -> keep
    await check(dut, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0])    # k>0 -> flip

    rng = random.Random(0xFACE0)

    # random normal-range (mix of hits from front and back)
    for _ in range(4000):
        n = [rng.uniform(-1, 1) for _ in range(3)]
        d = [rng.uniform(-1, 1) for _ in range(3)]
        await check(dut, n, d)

    # random wide-dynamic-range (rounding / cancellation near the k==0 boundary)
    for _ in range(4000):
        n = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        d = [rng.uniform(-1, 1) * 10 ** rng.randint(-12, 12) for _ in range(3)]
        await check(dut, n, d)

    dut._log.info("sobek_faceforward verified bit-exact vs golden "
                  "sobek_fp32.faceforward (8005 vectors)")
