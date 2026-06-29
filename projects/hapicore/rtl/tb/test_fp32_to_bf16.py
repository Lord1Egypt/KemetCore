"""cocotb testbench for HapiCore hapi_fp32_to_bf16 — bit-exact vs golden."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402


def f2b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


async def check(dut, u):
    dut.a.value = u
    await Timer(1, units="ns")
    exp = golden.fp32_to_bf16(u)
    assert int(dut.y.value) == exp, f"a={u:08x}: {int(dut.y.value):04x}!={exp:04x}"


def _nonnan(u):
    return not ((u & 0x7F800000) == 0x7F800000 and (u & 0x007FFFFF) != 0)


async def check_roundtrip(dut, u):
    # For non-NaN inputs, golden.fp32_to_bf16 must equal round_bf16's top 16 bits
    # (NaN payloads are canonicalised by the float round-trip, so skip them).
    if _nonnan(u):
        rb = struct.unpack("<I", struct.pack("<f", golden.round_bf16(
            struct.unpack("<f", struct.pack("<I", u))[0])))[0] >> 16
        assert golden.fp32_to_bf16(u) == (rb & 0xFFFF)


@cocotb.test()
async def test_fp32_to_bf16(dut):
    corners = [
        0x00000000, 0x80000000,                 # +/-0
        0x3F800000, 0xBF800000,                 # +/-1.0
        0x7F800000, 0xFF800000,                 # +/-Inf
        0x7FC00000, 0x7F800001, 0xFFABCDEF,     # NaNs (incl quirk cases)
        0x7F7FFFFF,                             # max finite -> rounds up to Inf
        0x3F808000, 0x3F818000, 0x3F807FFF,     # tie / above-tie / below-tie at bit16
        0x00000001, 0x007FFFFF,                 # subnormals
    ]
    for u in corners:
        await check(dut, u)
        await check_roundtrip(dut, u)
    for _ in range(20000):
        await check(dut, random.getrandbits(32))
    # dense sweep around the round/tie boundary for a fixed exponent
    base = 0x3F800000
    for low in range(0x0000, 0x20000, 7):
        await check(dut, (base | (low & 0xFFFF)) & 0xFFFFFFFF)
    dut._log.info("hapi_fp32_to_bf16 verified bit-exact vs golden")
