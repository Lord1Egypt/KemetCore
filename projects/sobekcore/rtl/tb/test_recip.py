"""cocotb testbench for SobekCore sobek_recip — fp32 reciprocal 1/x,
bit-exact vs the fp32 golden sobek_fp32.recip (combinational, no clock)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import sobek_fp32 as g  # noqa: E402


def fbits(x):
    """python float -> fp32 32-bit pattern."""
    return struct.unpack("<I", struct.pack("<f", x))[0]


async def check_bits(dut, xb):
    dut.x.value = xb
    await Timer(1, units="ns")
    got = int(dut.y.value)
    exp = g.recip_bits(xb)
    assert got == exp, f"recip({hex(xb)}): got {hex(got)} exp {hex(exp)}"


async def check(dut, x):
    await check_bits(dut, fbits(x))


@cocotb.test()
async def test_recip(dut):
    # directed cases
    await check(dut, 1.0)             # 1/1 = 1
    await check(dut, 2.0)             # 1/2 = 0.5 (exact)
    await check(dut, -4.0)            # negative
    await check(dut, 0.5)            # 1/0.5 = 2 (exact)
    await check(dut, 3.0)            # 1/3 rounds
    await check(dut, 1e30)          # tiny result
    await check(dut, 1e-30)         # large result

    rng = random.Random(0x1EC19)

    # random normal-range (avoid exact zero — det is nonzero past the parallel test)
    for _ in range(4000):
        x = rng.uniform(-1e3, 1e3)
        if abs(x) < 1e-6:
            x = 1.0
        await check(dut, x)

    # random wide-dynamic-range (rounding / overflow / underflow of the quotient)
    for _ in range(4000):
        x = rng.uniform(-1, 1) * 10 ** rng.randint(-20, 20)
        if x == 0.0:
            x = 1.0
        await check(dut, x)

    dut._log.info("sobek_recip verified bit-exact vs golden sobek_fp32.recip "
                  "(8007 values)")
