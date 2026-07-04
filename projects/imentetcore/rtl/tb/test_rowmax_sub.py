"""cocotb testbench for ImentetCore imentet_rowmax_sub — softmax stabilization
y = x - max(x), bit-exact vs golden imentet_fp32.rowmax_sub (combinational)."""
import math
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import imentet_fp32 as g  # noqa: E402

LS = g.LS


def fbits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def pack(vec):
    w = 0
    for i, u in enumerate(vec):
        w |= (u & 0xFFFFFFFF) << (32 * i)
    return w


async def check(dut, x):
    xb = [fbits(v) for v in x]
    dut.x.value = pack(xb)
    await Timer(1, units="ns")
    got = [(int(dut.y.value) >> (32 * i)) & 0xFFFFFFFF for i in range(LS)]
    exp = g.rowmax_sub_bits(xb)
    assert got == exp, f"rowmax_sub({x}): got {[hex(v) for v in got]} exp {[hex(v) for v in exp]}"


@cocotb.test()
async def test_rowmax_sub(dut):
    ninf = float("-inf")
    await check(dut, [1.0, 3.0, 2.0, 0.0, -1.0, 3.0, -5.0, 2.0])   # max 3
    await check(dut, [0.0] * LS)                                    # all equal -> zeros
    await check(dut, [ninf, 0.0, 1.0, ninf, 2.0, 0.0, -1.0, ninf]) # causal-masked row
    await check(dut, [-10.0, -20.0, -30.0, -5.0, -8.0, -1.0, -2.0, -9.0])  # all negative
    await check(dut, [5.0, 5.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0])    # tie at max

    rng = random.Random(0x50F72A)

    # random attention-logit-scale rows
    for _ in range(4000):
        x = [rng.uniform(-10, 10) for _ in range(LS)]
        await check(dut, x)

    # random rows with some causal -inf masking (never all -inf)
    for _ in range(4000):
        x = [rng.uniform(-10, 10) for _ in range(LS)]
        for i in range(LS):
            if rng.random() < 0.3:
                x[i] = float("-inf")
        if all(math.isinf(v) for v in x):
            x[0] = 0.0
        await check(dut, x)

    dut._log.info("imentet_rowmax_sub verified bit-exact vs golden "
                  "imentet_fp32.rowmax_sub (8005 vectors)")
