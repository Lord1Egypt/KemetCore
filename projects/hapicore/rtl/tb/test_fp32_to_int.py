"""cocotb testbench for HapiCore hapi_fp32_to_int — bit-exact vs golden + _f2i."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "..", "..", "..", "atumcore", "golden"))
from atum_rvv import VectorUnit  # noqa: E402


async def check(dut, a, signed, truncate):
    dut.a.value = a
    dut.is_signed.value = signed
    dut.truncate.value = truncate
    await Timer(1, units="ns")
    exp = golden.fp32_to_int(a, signed, truncate)
    assert exp == VectorUnit._f2i(a, signed, truncate), f"golden vs _f2i a={a:08x}"
    assert int(dut.y.value) == exp, \
        f"a={a:08x} s={signed} t={truncate}: {int(dut.y.value):08x}!={exp:08x}"


@cocotb.test()
async def test_fp32_to_int(dut):
    corners = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000,    # 0, -0, 1, -1
               0x4F000000, 0x4EFFFFFF, 0x5F000000, 0xCF000000,    # ~2^31 boundary
               0x4F7FFFFF, 0xCF000001, 0x437F0000, 0x47000000,
               0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001,    # +/-Inf, NaNs
               0x00000001, 0x807FFFFF, 0x3F000000, 0xBF000000,    # subnormal, 0.5
               0x4B000000, 0x4F800000, 0x5F800000]                # 2^23, 2^32, huge
    for s in (0, 1):
        for t in (0, 1):
            for a in corners:
                await check(dut, a, s, t)
    for _ in range(40000):
        await check(dut, random.getrandbits(32), random.randint(0, 1), random.randint(0, 1))
    dut._log.info("hapi_fp32_to_int verified bit-exact vs golden + AtumCore _f2i")
