"""cocotb testbench for HapiCore hapi_fp32_sgnj — bit-exact vs golden fp32_sgnj."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


async def check(dut, a, b, op):
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, units="ns")
    exp = golden.fp32_sgnj(a, b, op)
    assert int(dut.y.value) == exp, f"op={op} a={a:08x} b={b:08x}: {int(dut.y.value):08x}!={exp:08x}"


@cocotb.test()
async def test_fp32_sgnj(dut):
    corners = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000,
               0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001, 0x007FFFFF]
    for op in range(3):
        for a in corners:
            for b in corners:
                await check(dut, a, b, op)
    for _ in range(6000):
        await check(dut, random.getrandbits(32), random.getrandbits(32), random.randint(0, 2))
    dut._log.info("hapi_fp32_sgnj verified bit-exact vs golden")
