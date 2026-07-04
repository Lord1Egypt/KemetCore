"""cocotb testbench for HapiCore hapi_bf16_cmp — bit-exact vs golden bf16_cmp."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


async def check(dut, a, b, op):
    dut.a.value = a; dut.b.value = b; dut.op.value = op
    await Timer(1, units="ns")
    exp = golden.bf16_cmp(a, b, op)
    assert int(dut.y.value) == exp, f"op={op} a={a:04x} b={b:04x}: {int(dut.y.value)}!={exp}"


@cocotb.test()
async def test_bf16_cmp(dut):
    corners = [0x0000, 0x8000, 0x3F80, 0xBF80, 0x4000, 0xC000,
               0x7F80, 0xFF80, 0x7FC0, 0x7F81, 0xFFFF, 0x0001, 0x8001, 0x007F, 0x807F]
    for op in range(3):
        for a in corners:
            for b in corners:
                await check(dut, a, b, op)
    for _ in range(12000):
        await check(dut, random.getrandbits(16), random.getrandbits(16), random.randint(0, 2))
    dut._log.info("hapi_bf16_cmp verified bit-exact vs golden bf16_cmp")
