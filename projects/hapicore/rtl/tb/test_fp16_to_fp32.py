"""cocotb testbench for HapiCore hapi_fp16_to_fp32 — bit-exact vs numpy."""
import os
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


async def check(dut, h):
    dut.a.value = h
    await Timer(1, units="ns")
    exp = golden.fp16_to_fp32(h)
    assert int(dut.y.value) == exp, f"a={h:04x}: {int(dut.y.value):08x}!={exp:08x}"


@cocotb.test()
async def test_fp16_to_fp32(dut):
    # exhaustive over all 65536 fp16 bit patterns (the upcast is exact)
    for h in range(0x10000):
        await check(dut, h)
    dut._log.info("hapi_fp16_to_fp32 verified bit-exact vs numpy on all 65536 patterns")
