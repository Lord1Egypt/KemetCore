"""cocotb testbench for ImentetCore imentet_mask_add — additive attention mask
y = x + m, bit-exact vs golden imentet_fp32.mask_add (combinational)."""
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


async def check(dut, x, m):
    xb = [fbits(v) for v in x]
    mb = [fbits(v) for v in m]
    dut.x.value = pack(xb)
    dut.m.value = pack(mb)
    await Timer(1, units="ns")
    got = [(int(dut.y.value) >> (32 * i)) & 0xFFFFFFFF for i in range(LS)]
    exp = g.mask_add_bits(xb, mb)
    assert got == exp, f"mask_add: got {[hex(v) for v in got]} exp {[hex(v) for v in exp]}"


@cocotb.test()
async def test_mask_add(dut):
    ninf = float("-inf")
    await check(dut, [float(i) for i in range(LS)], [0.0] * LS)                 # no mask
    await check(dut, [1.0] * LS, [0.0, 0.0, 0.0, ninf, 0.0, ninf, 0.0, 0.0])   # causal holes
    await check(dut, [2.0] * LS, [ninf] * LS)                                   # all masked
    await check(dut, [-3.0, 4.0, -1.0, 2.0, 0.0, 5.0, -2.0, 1.0], [0.0] * LS)

    rng = random.Random(0x3A5C0D)

    # causal-style: lower triangle 0, upper -inf, random logits
    for _ in range(4000):
        x = [rng.uniform(-10, 10) for _ in range(LS)]
        cut = rng.randint(0, LS)
        m = [0.0 if j < cut else ninf for j in range(LS)]
        await check(dut, x, m)

    # random additive biases (not just 0/-inf: relative-position style)
    for _ in range(4000):
        x = [rng.uniform(-1, 1) * 10 ** rng.randint(-6, 6) for _ in range(LS)]
        m = [rng.uniform(-1, 1) * 10 ** rng.randint(-6, 6) for _ in range(LS)]
        await check(dut, x, m)

    dut._log.info("imentet_mask_add verified bit-exact vs golden "
                  "imentet_fp32.mask_add (8004 vectors)")
