"""cocotb testbench for GebCore geb_compress — 2:4 metadata compression,
bit-exact vs golden geb_sparse.compress_group (combinational)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import geb_sparse as g  # noqa: E402


def f2b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def b2f(u):
    return struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0]


async def check(dut, lanes):
    word = 0
    for i, v in enumerate(lanes):
        word |= (f2b(v) & 0xFFFFFFFF) << (32 * i)
    dut.group.value = word
    await Timer(1, units="ns")
    ev0, ei0, ev1, ei1 = g.compress_group(lanes)
    assert int(dut.idx0.value) == ei0, f"{lanes}: idx0 {int(dut.idx0.value)}!={ei0}"
    assert int(dut.idx1.value) == ei1, f"{lanes}: idx1 {int(dut.idx1.value)}!={ei1}"
    assert int(dut.val0.value) == f2b(float(ev0)), f"{lanes}: val0 mismatch"
    assert int(dut.val1.value) == f2b(float(ev1)), f"{lanes}: val1 mismatch"


@cocotb.test()
async def test_compress(dut):
    # directed: every count/position of nonzeros
    await check(dut, [0.0, 2.5, 0.0, -4.0])       # 2 kept at 1,3
    await check(dut, [1.0, 2.0, 3.0, 4.0])        # 4 nonzero -> take 0,1
    await check(dut, [0.0, 0.0, 7.0, 0.0])        # 1 nonzero -> 2,0
    await check(dut, [0.0, 0.0, 0.0, 0.0])        # all zero -> 0,1
    await check(dut, [-0.0, 3.0, 0.0, 5.0])       # -0 counts as zero -> 1,3
    await check(dut, [5.0, 0.0, 0.0, 6.0])        # 0,3

    rng = random.Random(0x6EB2C0)
    # random well-formed pruned groups (exactly 2 nonzero) + random arbitrary groups
    for _ in range(3000):
        vals = [0.0, 0.0, 0.0, 0.0]
        keep = rng.sample(range(4), 2)
        for k in keep:
            vals[k] = rng.uniform(-100, 100) or 1.0
        await check(dut, vals)
    for _ in range(3000):
        vals = [rng.choice([0.0, rng.uniform(-1e3, 1e3)]) for _ in range(4)]
        await check(dut, vals)

    dut._log.info("geb_compress verified bit-exact vs golden compress_group (6006 groups)")
