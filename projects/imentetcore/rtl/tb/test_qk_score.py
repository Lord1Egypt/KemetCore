"""cocotb testbench for ImentetCore imentet_qk_score — fp32 scaled dot-product
attention score, bit-exact vs the fp32 golden imentet_fp32.score (combinational)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import imentet_fp32 as g  # noqa: E402

D = g.D


def fbits(x):
    """python float -> fp32 32-bit pattern."""
    return struct.unpack("<I", struct.pack("<f", x))[0]


def pack(vec):
    """list of D fp32 patterns -> 32*D-bit little-endian word (element i at bits 32*i)."""
    w = 0
    for i, u in enumerate(vec):
        w |= (u & 0xFFFFFFFF) << (32 * i)
    return w


async def check(dut, q, k, s):
    qb = [fbits(x) for x in q]
    kb = [fbits(x) for x in k]
    sb = fbits(s)
    dut.q.value = pack(qb)
    dut.k.value = pack(kb)
    dut.s.value = sb
    await Timer(1, units="ns")
    got = int(dut.score.value)
    exp = g.score_bits(qb, kb, sb)
    assert got == exp, f"score({q},{k},{s}): got {hex(got)} exp {hex(exp)}"


@cocotb.test()
async def test_qk_score(dut):
    inv_sqrt_d = 1.0 / (D ** 0.5)

    # directed cases
    await check(dut, [1.0] * D, [1.0] * D, inv_sqrt_d)          # sum=D, scaled
    await check(dut, [0.0] * D, [1.0] * D, inv_sqrt_d)          # zero query
    await check(dut, list(range(D)), [1.0] * D, 1.0)           # 0+1+..+7 = 28
    await check(dut, [1.0] * D, [-1.0] * D, inv_sqrt_d)        # negative
    await check(dut, [2.0] * D, [0.5] * D, 1.0)               # each product 1 -> D

    rng = random.Random(0x1CE2C0)

    # random normal-range (attention logits are typically O(1) after scaling)
    for _ in range(4000):
        q = [rng.uniform(-4, 4) for _ in range(D)]
        k = [rng.uniform(-4, 4) for _ in range(D)]
        await check(dut, q, k, inv_sqrt_d)

    # random wide-dynamic-range (exercise rounding / cancellation / overflow)
    for _ in range(4000):
        q = [rng.uniform(-1, 1) * 10 ** rng.randint(-10, 10) for _ in range(D)]
        k = [rng.uniform(-1, 1) * 10 ** rng.randint(-10, 10) for _ in range(D)]
        s = rng.uniform(-1, 1) * 10 ** rng.randint(-4, 4)
        await check(dut, q, k, s)

    dut._log.info("imentet_qk_score verified bit-exact vs golden imentet_fp32.score "
                  "(8005 vectors)")
