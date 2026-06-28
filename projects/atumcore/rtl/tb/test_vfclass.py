"""cocotb testbench for atum_vfclass — the AtumCore fp32 classify unit.

Drives a random fp32 vector and VL, and compares every lane's 10-bit class against
the golden VectorUnit.vfclass (tail lanes 0).
"""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8
ELEN = 32
MASKW = (1 << ELEN) - 1

SPECIALS = [0x00000000, 0x80000000,           # +0, -0
            0x3F800000, 0xBF800000,           # +1 (+normal), -1 (-normal)
            0x00000001, 0x80000001,           # +subnormal, -subnormal
            0x7F800000, 0xFF800000,           # +inf, -inf
            0x7FC00000, 0x7F800001,           # qNaN, sNaN
            0xFFC00001, 0x7F7FFFFF]           # -qNaN, +max normal


def fbits():
    return struct.unpack("<I", struct.pack("<f", random.uniform(-1e6, 1e6)))[0]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    return [int(x) for x in vu.vfclass(1)]


async def check(dut, vs, vl):
    dut.vs.value = pack(vs)
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"lane{i} vl={vl} x={vs[i]:08x}: got {got[i]:010b} != golden {exp[i]:010b}")


@cocotb.test()
async def test_directed(dut):
    """Every fp class (+/-0, +/-sub, +/-normal, +/-inf, sNaN, qNaN) and vl gating."""
    a = SPECIALS[:VLMAX]
    b = SPECIALS[4:4 + VLMAX]
    await check(dut, a, 8)
    await check(dut, b, 8)
    await check(dut, a, 3)            # vl gating -> tail 0
    await check(dut, a, 0)            # vl=0 -> all 0
    dut._log.info("atum_vfclass: directed fp class corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC1A55)
    random.seed(0xC1A55)
    for _ in range(8000):
        vs = [rng.choice(SPECIALS) if rng.random() < 0.5 else fbits()
              for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, vl)
    dut._log.info("atum_vfclass: 8000 random classifications match golden")
