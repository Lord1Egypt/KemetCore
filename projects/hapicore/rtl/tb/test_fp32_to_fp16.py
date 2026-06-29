"""cocotb testbench for HapiCore hapi_fp32_to_fp16 — bit-exact vs numpy float16."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


async def check(dut, u):
    dut.a.value = u
    await Timer(1, units="ns")
    exp = golden.fp32_to_fp16(u)
    assert int(dut.y.value) == exp, f"a={u:08x}: {int(dut.y.value):04x}!={exp:04x}"


@cocotb.test()
async def test_fp32_to_fp16(dut):
    corners = [
        0x00000000, 0x80000000,                # +/-0
        0x3F800000, 0xBF800000,                # +/-1
        0x7F800000, 0xFF800000,                # +/-Inf
        0x7FC00000, 0x7F800001, 0xFFABCDEF,    # NaN
        0x477FE000, 0x477FF000, 0x47800000,    # near fp16 max / overflow boundary
        0x38800000, 0x38000000, 0x33800000,    # small normals / subnormal region
        0x33000000, 0x32000000, 0x00000001,    # underflow to 0 / fp32 subnormal
        0x387FC000, 0x387FE000,                # subnormal rounding boundary
    ]
    for u in corners:
        await check(dut, u)
    # sweep every fp32 exponent with a few mantissas + signs (covers all regimes)
    for e in range(0, 256):
        for m in [0, 1, 0x1000, 0x1FFF, 0x400000, 0x7FE000, 0x7FFFFF]:
            for s in (0, 1):
                await check(dut, (s << 31) | (e << 23) | m)
    for _ in range(30000):
        await check(dut, random.getrandbits(32))
    dut._log.info("hapi_fp32_to_fp16 verified bit-exact vs numpy float16")
