"""cocotb testbench for HapiCore hapi_bf16_to_fp32 — bit-exact vs golden."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


@cocotb.test()
async def test_bf16_to_fp32(dut):
    for h in range(0x10000):
        dut.a.value = h
        await Timer(1, units="ns")
        exp = golden.bf16_to_fp32(h)
        assert int(dut.y.value) == exp, f"a={h:04x}: {int(dut.y.value):08x}!={exp:08x}"
    dut._log.info("hapi_bf16_to_fp32 verified bit-exact vs golden on all 65536 patterns")
