"""cocotb testbench for ImentetCore imentet_softmax_norm — fp32 softmax
normalization p = e/sum(e), bit-exact vs golden imentet_fp32.softmax_norm."""
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


async def check(dut, e):
    eb = [fbits(v) for v in e]
    dut.e.value = pack(eb)
    await Timer(1, units="ns")
    got = [(int(dut.p.value) >> (32 * i)) & 0xFFFFFFFF for i in range(LS)]
    exp = g.softmax_norm_bits(eb)
    assert got == exp, f"softmax_norm({e}): got {[hex(v) for v in got]} exp {[hex(v) for v in exp]}"


@cocotb.test()
async def test_softmax_norm(dut):
    import math
    await check(dut, [1.0] * LS)                       # uniform -> 1/LS
    e = [0.0] * LS; e[3] = 5.0
    await check(dut, e)                                # one-hot -> delta
    await check(dut, [float(i + 1) for i in range(LS)])  # increasing weights
    # realistic post-exp weights (exp of stabilized logits in [-something,0] -> (0,1])
    await check(dut, [math.exp(v) for v in (-3.0, -1.0, 0.0, -2.0, -0.5, -4.0, -1.5, -0.1)])

    rng = random.Random(0x50F7A2)

    # random post-exp weights (non-negative, from exp of stabilized logits)
    for _ in range(4000):
        e = [math.exp(rng.uniform(-12, 0)) for _ in range(LS)]
        await check(dut, e)

    # random positive wide-range (rounding / sum overflow of the divide)
    for _ in range(4000):
        e = [rng.uniform(0, 1) * 10 ** rng.randint(-6, 6) for _ in range(LS)]
        if sum(e) == 0.0:
            e[0] = 1.0
        await check(dut, e)

    dut._log.info("imentet_softmax_norm verified bit-exact vs golden "
                  "imentet_fp32.softmax_norm (8004 vectors)")
