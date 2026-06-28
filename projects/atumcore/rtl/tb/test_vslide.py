"""cocotb testbench for atum_vslide — the AtumCore vector slide unit.

Drives a random source vector, scalar offset, op (slideup/slidedown) and VL, and
compares every lane of the slid result against the golden VectorUnit.vslideup /
vslidedown (out-of-range source lanes and the tail read 0).
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8
ELEN = 32
MASKW = (1 << ELEN) - 1


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs, off, op, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    res = vu.vslidedown(1, off) if op else vu.vslideup(1, off)
    return [int(x) for x in res]


async def check(dut, vs, off, op, vl):
    dut.vs.value = pack(vs)
    dut.off.value = off
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs, off, op, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"op={'down' if op else 'up'} lane{i} off={off} vl={vl}: "
            f"got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """Corners: offset 0 (identity), offset 1, offset >= vl (all 0), vl gating."""
    vs = [0xA0, 0xB1, 0xC2, 0xD3, 0xE4, 0xF5, 0x16, 0x27]
    for op in (0, 1):
        await check(dut, vs, 0, op, 8)     # identity within vl
        await check(dut, vs, 1, op, 8)
        await check(dut, vs, 3, op, 8)
        await check(dut, vs, 8, op, 8)     # offset == vl -> all 0
        await check(dut, vs, 100, op, 8)   # huge offset -> all 0
        await check(dut, vs, 2, op, 5)     # partial vl
    dut._log.info("atum_vslide: directed slide corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x511DE)
    for _ in range(8000):
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        op = rng.randint(0, 1)
        off = rng.choice([rng.randint(0, VLMAX), rng.getrandbits(32)])
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, off, op, vl)
    dut._log.info("atum_vslide: 8000 random slides match golden")
