"""cocotb testbench for HapiCore hapi_fp16_class — bit-exact vs golden fp16_class.
Exhaustive over all 65536 fp16 bit patterns."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


@cocotb.test()
async def test_fp16_class(dut):
    for a in range(1 << 16):
        dut.a.value = a
        await Timer(1, units="ns")
        exp = golden.fp16_class(a)
        assert int(dut.y.value) == exp, f"a={a:04x}: {int(dut.y.value):03x}!={exp:03x}"
    dut._log.info("hapi_fp16_class verified bit-exact vs golden (exhaustive 65536 inputs)")
