"""cocotb testbench for atum_vmv — the AtumCore vector move unit (splat / copy)."""
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
    res = vu.vmv_vv(1) if op else vu.vmv_vx(x)
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
            f"op={'vv' if op else 'vx'} lane{i} vl={vl}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    vs = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]
    await check(dut, 0, vs, 0xDEADBEEF, 8)   # splat
    await check(dut, 1, vs, 0xDEADBEEF, 8)   # copy
    await check(dut, 0, vs, 0x00000000, 4)   # splat zero, vl gating
    await check(dut, 1, vs, 0, 0)            # vl=0 -> all 0
    dut._log.info("atum_vmv: directed splat/copy corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x713A)
    for _ in range(6000):
        op = rng.randint(0, 1)
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        x = rng.getrandbits(32)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, vs, x, vl)
    dut._log.info("atum_vmv: 6000 random splat/copy match golden")
