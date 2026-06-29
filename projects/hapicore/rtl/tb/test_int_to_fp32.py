"""cocotb testbench for HapiCore hapi_int_to_fp32 — bit-exact vs golden + numpy."""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


def ref(x, is_signed):
    iv = np.int32(np.uint32(x)) if is_signed else np.uint32(x)
    return int(np.frombuffer(struct.pack("<f", np.float32(iv)), np.uint32)[0])


async def check(dut, x, is_signed):
    dut.x.value = x
    dut.is_signed.value = is_signed
    await Timer(1, units="ns")
    exp = golden.int_to_fp32(x, is_signed)
    assert exp == ref(x, is_signed), f"golden vs numpy x={x:08x} s={is_signed}"
    assert int(dut.y.value) == exp, f"x={x:08x} s={is_signed}: {int(dut.y.value):08x}!={exp:08x}"


@cocotb.test()
async def test_int_to_fp32(dut):
    corners = [0, 1, 2, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0x00FFFFFF,
               0x01000000, 0x01000001, 0xFF000000, 0x12345678, 0x00800000]
    for s in (0, 1):
        for x in corners:
            await check(dut, x, s)
        # all values whose magnitude fits exactly (<= 24 bits): exact, no rounding
        for x in range(0, 1 << 16):
            await check(dut, x, s)
    # random 32-bit (exercises rounding for >24-bit magnitudes)
    for _ in range(40000):
        await check(dut, random.getrandbits(32), random.randint(0, 1))
    dut._log.info("hapi_int_to_fp32 verified bit-exact vs golden + numpy")
