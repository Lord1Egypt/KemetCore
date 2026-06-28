"""cocotb testbench for atum_vslide1 — the AtumCore vector slide-by-1 unit."""
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


def golden(op, vs, x, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    res = vu.vslide1down(1, x) if op else vu.vslide1up(1, x)
    return [int(v) for v in res]


async def check(dut, op, vs, x, vl):
    dut.vs.value = pack(vs)
    dut.x.value = x
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(op, vs, x, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"op={'down' if op else 'up'} lane{i} vl={vl}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    vs = [10, 11, 12, 13, 14, 15, 16, 17]
    await check(dut, 0, vs, 0x99, 8)   # slide1up full
    await check(dut, 1, vs, 0x99, 8)   # slide1down full
    await check(dut, 0, vs, 0x99, 4)   # slide1up vl=4
    await check(dut, 1, vs, 0x99, 4)   # slide1down vl=4 (x lands at lane3)
    await check(dut, 0, vs, 0x99, 1)   # vl=1: up -> [x]; down -> [x]
    await check(dut, 1, vs, 0x99, 1)
    await check(dut, 0, vs, 0x99, 0)   # vl=0 -> all 0
    dut._log.info("atum_vslide1: directed slide-by-1 corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x511D1)
    for _ in range(6000):
        op = rng.randint(0, 1)
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        x = rng.getrandbits(32)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, vs, x, vl)
    dut._log.info("atum_vslide1: 6000 random slide-by-1 ops match golden")
