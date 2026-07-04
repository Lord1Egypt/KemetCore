"""cocotb testbench for ImentetCore imentet_av_context — fp32 weighted value
accumulation context=P·V, bit-exact vs golden imentet_fp32.av_context."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import imentet_fp32 as g  # noqa: E402

L, DV = g.L, g.DV


def fbits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def packv(vec):
    w = 0
    for i, u in enumerate(vec):
        w |= (u & 0xFFFFFFFF) << (32 * i)
    return w


async def check(dut, w, V):
    wb = [fbits(x) for x in w]
    Vb = [fbits(V[j][k]) for j in range(L) for k in range(DV)]
    dut.w.value = packv(wb)
    dut.v.value = packv(Vb)
    await Timer(1, units="ns")
    got = [(int(dut.ctx.value) >> (32 * k)) & 0xFFFFFFFF for k in range(DV)]
    exp = g.av_context_bits(wb, Vb)
    assert got == exp, f"av_context: got {[hex(x) for x in got]} exp {[hex(x) for x in exp]}"


@cocotb.test()
async def test_av_context(dut):
    # directed
    await check(dut, [0.25] * L, [[1.0, 0.0, 0.0, 0.0], [0.0, 2.0, 0.0, 0.0],
                                  [0.0, 0.0, 3.0, 0.0], [0.0, 0.0, 0.0, 4.0]])
    await check(dut, [1.0, 0.0, 0.0, 0.0], [[5.0, 6.0, 7.0, 8.0]] + [[0.0] * DV] * 3)  # pick row 0
    await check(dut, [0.5, 0.5, 0.0, 0.0], [[2.0] * DV, [4.0] * DV, [0.0] * DV, [0.0] * DV])

    rng = random.Random(0xA7C0DE)

    # random softmax-like weights (non-negative, sum≈1) + O(1) values
    for _ in range(4000):
        raw = [rng.random() for _ in range(L)]
        tot = sum(raw)
        w = [r / tot for r in raw]
        V = [[rng.uniform(-4, 4) for _ in range(DV)] for _ in range(L)]
        await check(dut, w, V)

    # random wide-dynamic-range
    for _ in range(4000):
        w = [rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(L)]
        V = [[rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(DV)] for _ in range(L)]
        await check(dut, w, V)

    dut._log.info("imentet_av_context verified bit-exact vs golden "
                  "imentet_fp32.av_context (8003 vectors)")
