"""cocotb testbench for atum_vssr — the AtumCore scaling shift-right (rounding) unit.

Each trial randomises the value vector vs1, the shift-amount vector vs2, VL and the
per-lane mask, drives the combinational lane array, and compares every lane against
the golden VectorUnit.vssrl / vssra (round-to-nearest-up). Operands cross the boundary
packed little-endian by lane: element i at bits [i*32 +: 32].
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

OPS = {0: "vssrl", 1: "vssra"}

CORNERS = [0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 0x80000001,
           0xC0000000, 0x40000000, 3, 0xFFFFFFFE]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(op, vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    getattr(vu, OPS[op])(3, 1, 2, mask=mask)
    return [int(x) for x in vu.vreg[3].astype(np.uint32)]


async def check(dut, op, vs1, vs2, vd_old, vl, mask_bits):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.vd_old.value = pack(vd_old)
    dut.op.value = op
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = unpack(dut.vd_new.value)
    exp = golden(op, vs1, vs2, vd_old, vl, mask_bits)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"{OPS[op]} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} "
            f"(v={vs1[i]:08x} sh={vs2[i] & 31})")


@cocotb.test()
async def test_directed(dut):
    old = [0x33333333] * VLMAX
    shifts = [0, 1, 2, 1, 31, 4, 1, 8]
    await check(dut, 0, CORNERS[:VLMAX], shifts, old, 8, 0xFF)
    await check(dut, 1, CORNERS[:VLMAX], shifts, old, 8, 0xFF)
    # sh=0 -> identity (no rounding)
    await check(dut, 0, CORNERS[:VLMAX], [0] * VLMAX, old, 8, 0xFF)
    await check(dut, 1, CORNERS[:VLMAX], [0] * VLMAX, old, 8, 0xFF)
    # rounding: 3 >> 1 -> 2 (rnu), 1 >> 1 -> 1
    await check(dut, 0, [3, 1, 5, 7, 6, 0xFFFFFFFF, 2, 9], [1] * VLMAX, old, 8, 0xFF)
    await check(dut, 0, CORNERS[:VLMAX], shifts, old, 0, 0xFF)         # vl=0
    await check(dut, 1, CORNERS[:VLMAX], shifts, old, 5, 0b10101)      # partial+mask
    dut._log.info("atum_vssr: directed rounding-shift corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5523)
    for _ in range(6000):
        op = rng.randint(0, 1)

        def rv():
            return rng.choice(CORNERS) if rng.random() < 0.4 else rng.getrandbits(32)
        vs1 = [rv() for _ in range(VLMAX)]
        vs2 = [rng.getrandbits(32) for _ in range(VLMAX)]   # full word; low 5 bits used
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vssr: 6000 random rounding shifts match golden (vssrl/vssra)")
