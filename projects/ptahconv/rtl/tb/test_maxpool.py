"""cocotb testbench for PtahConv ptah_maxpool — fp32 2x2 max-pooling,
bit-exact vs golden ptah_conv.maxpool2x2 (combinational)."""
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


async def check(dut, a, b, c, d):
    dut.a.value = a; dut.b.value = b; dut.c.value = c; dut.d.value = d
    await Timer(1, units="ns")
    exp = golden.maxpool2x2(a, b, c, d)
    got = int(dut.y.value)
    assert got == exp, f"maxpool({a:08x},{b:08x},{c:08x},{d:08x}): {got:08x}!={exp:08x}"


@cocotb.test()
async def test_maxpool(dut):
    corners = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x40000000, 0xC0000000,
               0x7F800000, 0xFF800000, 0x00800000, 0x80800000]
    for a in corners:
        for b in corners:
            await check(dut, a, b, corners[0], corners[-1])
    rng = random.Random(0x4A2900)
    # post-relu-like non-negative finite windows (the common maxpool domain)
    for _ in range(4000):
        def relu_val():
            exp = rng.randint(110, 140)
            return (exp << 23) | rng.getrandbits(23)   # sign 0 -> non-negative
        await check(dut, relu_val(), relu_val(), relu_val(), relu_val())
    # fully random (signed, incl inf/subnormal/nan patterns) — total-order max
    for _ in range(4000):
        await check(dut, rng.getrandbits(32), rng.getrandbits(32),
                    rng.getrandbits(32), rng.getrandbits(32))
    dut._log.info("ptah_maxpool verified bit-exact vs golden maxpool2x2 (8100 windows)")
