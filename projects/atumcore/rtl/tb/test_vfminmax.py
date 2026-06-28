"""cocotb testbench for atum_vfminmax — the AtumCore fp32 min/max unit.

Drives two random fp32 vectors, op (min/max) and VL, and compares every lane of
the result against the golden VectorUnit.vfmin / vfmax (NaN propagation, canonical
NaN when both NaN, -0 below +0). Random pool is biased toward special fp classes.
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
            0x3F800000, 0xBF800000,           # +1, -1
            0x7F800000, 0xFF800000,           # +inf, -inf
            0x7FC00000, 0x7F800001,           # qNaN, sNaN
            0x00000001, 0x80000001,           # +/- smallest subnormal
            0x40490FDB, 0xC0490FDB]           # +/- pi


def fbits():
    return struct.unpack("<I", struct.pack("<f", random.uniform(-1e6, 1e6)))[0]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs1, vs2, op, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vl = vl
    res = vu.vfmax(1, 2) if op else vu.vfmin(1, 2)
    return [int(x) for x in res]


async def check(dut, vs1, vs2, op, vl):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs1, vs2, op, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"op={'max' if op else 'min'} lane{i} vl={vl} "
            f"a={vs1[i]:08x} b={vs2[i]:08x}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """All special-class pairings (+/-0, +/-inf, NaN, pi, subnormal) for min and max."""
    a = (SPECIALS + SPECIALS)[:VLMAX]
    b = (SPECIALS[::-1] + SPECIALS)[:VLMAX]
    for op in (0, 1):
        await check(dut, a, b, op, 8)
        await check(dut, a, b, op, 3)                 # vl gating
        # -0 vs +0 must give -0 (min) / +0 (max)
        await check(dut, [0x80000000] * 8, [0x00000000] * 8, op, 8)
        # NaN vs number -> number; both NaN -> canonical
        await check(dut, [0x7FC00000] * 8, [0x3F800000] * 8, op, 8)
        await check(dut, [0x7FC00000] * 8, [0xFF800123] * 8, op, 8)
    dut._log.info("atum_vfminmax: directed fp min/max corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xF312)
    random.seed(0xF312)
    for _ in range(8000):
        a = [rng.choice(SPECIALS) if rng.random() < 0.4 else fbits()
             for _ in range(VLMAX)]
        b = [rng.choice(SPECIALS) if rng.random() < 0.4 else fbits()
             for _ in range(VLMAX)]
        op = rng.randint(0, 1)
        vl = rng.randint(0, VLMAX)
        await check(dut, a, b, op, vl)
    dut._log.info("atum_vfminmax: 8000 random fp min/max match golden")
