"""cocotb testbench for HapiCore hapi_fp32_class — bit-exact vs golden fp32_class."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


async def check(dut, a):
    dut.a.value = a
    await Timer(1, units="ns")
    exp = golden.fp32_class(a)
    assert int(dut.y.value) == exp, f"a={a:08x}: {int(dut.y.value):010b}!={exp:010b}"


@cocotb.test()
async def test_fp32_class(dut):
    corners = [0x00000000, 0x80000000,         # +/-0
               0x3F800000, 0xBF800000,         # +/-normal
               0x00000001, 0x80000001,         # +/-subnormal
               0x007FFFFF, 0x807FFFFF,         # +/-max subnormal
               0x7F800000, 0xFF800000,         # +/-Inf
               0x7FC00000,                     # quiet NaN (man MSB set)
               0x7F800001, 0xFF800001,         # signaling NaN (man MSB clear)
               0x7FFFFFFF, 0xFFBFFFFF]
    for a in corners:
        await check(dut, a)
    for _ in range(20000):
        await check(dut, random.getrandbits(32))
    dut._log.info("hapi_fp32_class verified bit-exact vs golden")
