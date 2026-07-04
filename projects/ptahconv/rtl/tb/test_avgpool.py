"""cocotb testbench for PtahConv ptah_avgpool — fp32 2x2 average-pooling,
bit-exact vs golden ptah_conv.avgpool2x2 (combinational)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ptah_conv as golden  # noqa: E402


def f2b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def check(dut, a, b, c, d):
    dut.a.value = a; dut.b.value = b; dut.c.value = c; dut.d.value = d
    await Timer(1, units="ns")
    exp = golden.avgpool2x2(a, b, c, d)
    got = int(dut.y.value)
    if is_nan32(exp):
        assert is_nan32(got), f"avgpool({a:08x},{b:08x},{c:08x},{d:08x}): got {got:08x}, expected NaN"
    else:
        assert got == exp, f"avgpool({a:08x},{b:08x},{c:08x},{d:08x}): {got:08x}!={exp:08x}"


@cocotb.test()
async def test_avgpool(dut):
    # exact directed: mean of 4 known values
    await check(dut, f2b(1.0), f2b(2.0), f2b(3.0), f2b(4.0))   # (10)*0.25 = 2.5
    await check(dut, f2b(0.0), f2b(0.0), f2b(0.0), f2b(0.0))   # 0
    await check(dut, f2b(-1.0), f2b(1.0), f2b(-1.0), f2b(1.0)) # 0
    corners = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000, 0xFF800000,
               0x7FC00000, 0x00800000]
    for a in corners:
        for b in corners:
            await check(dut, a, b, corners[2], corners[3])

    rng = random.Random(0x4A6900)
    for _ in range(4000):
        def tame():
            sign = rng.getrandbits(1) << 31
            exp = rng.randint(112, 138)
            return sign | (exp << 23) | rng.getrandbits(23)
        await check(dut, tame(), tame(), tame(), tame())
    for _ in range(4000):
        await check(dut, rng.getrandbits(32), rng.getrandbits(32),
                    rng.getrandbits(32), rng.getrandbits(32))
    dut._log.info("ptah_avgpool verified bit-exact vs golden avgpool2x2 (8067 windows)")
