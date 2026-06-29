"""cocotb testbench for atum_vredminmax — AtumCore integer min/max reduction.

Each trial randomises an integer source vector, op (minu/maxu/mins/maxs), VL and the
per-lane mask, drives the combinational fold chain, and compares the scalar result
against the golden VectorUnit (identity-seeded left-to-right fold).
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
GMETH = ["vredminu", "vredmaxu", "vredmins", "vredmaxs"]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def golden(op, vs, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[2] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    return getattr(vu, GMETH[op])(2, mask=mask)


async def check(dut, op, vs, vl, mask_bits):
    dut.vs.value = pack(vs)
    dut.op.value = op
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = int(dut.result.value)
    exp = golden(op, vs, vl, mask_bits)
    assert got == exp, (
        f"{GMETH[op]} vl={vl} mask={mask_bits:08b}: got {got:08x} != golden {exp:08x} "
        f"(vs={[f'{x:08x}' for x in vs]})")


@cocotb.test()
async def test_directed(dut):
    vals = [5, 0xFFFFFFFF, 0x80000000, 3, 0x7FFFFFFF, 1, 0xFFFFFFF0, 100]
    for op in range(4):
        await check(dut, op, vals, 8, 0xFF)
        await check(dut, op, vals, 0, 0xFF)          # empty -> identity
        await check(dut, op, vals, 5, 0b00101)
        await check(dut, op, vals, 8, 0b10101010)
    dut._log.info("atum_vredminmax: directed (signed/unsigned extremes, empty) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0FFEE)
    for _ in range(8000):
        op = rng.randint(0, 3)
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs, vl, mask)
    dut._log.info("atum_vredminmax: 8000 random int min/max reductions match golden")
