"""cocotb testbench for atum_vsmul — the AtumCore signed Q31 fractional multiply.

Each trial randomises the two source vectors, VL and the per-lane mask, drives the
combinational lane array, and compares every lane against the golden VectorUnit.vsmul
(round-to-nearest-up by 31 fractional bits, then signed saturation). Operands cross
the boundary packed little-endian by lane: element i at bits [i*32 +: 32].
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

CORNERS = [0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 0x40000000,
           0xC0000000, 0x00010000, 0x7FFF0000, 2]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    vu.vsmul(3, 1, 2, mask=mask)
    return [int(x) for x in vu.vreg[3].astype(np.uint32)]


async def check(dut, vs1, vs2, vd_old, vl, mask_bits):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.vd_old.value = pack(vd_old)
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = unpack(dut.vd_new.value)
    exp = golden(vs1, vs2, vd_old, vl, mask_bits)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"vsmul lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} (a={vs1[i]:08x} b={vs2[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    old = [0x5A5A5A5A] * VLMAX
    await check(dut, CORNERS[:VLMAX], CORNERS[2:2 + VLMAX], old, 8, 0xFF)
    # the saturating case: INT_MIN * INT_MIN (Q31 -1*-1 = +1.0) -> INT_MAX
    await check(dut, [0x80000000] * VLMAX, [0x80000000] * VLMAX, old, 8, 0xFF)
    # +1.0(Q31)=INT_MAX times values; -0.5 etc
    await check(dut, [0x7FFFFFFF] * VLMAX, [0x40000000] * VLMAX, old, 8, 0xFF)
    await check(dut, CORNERS[:VLMAX], CORNERS[2:2 + VLMAX], old, 0, 0xFF)   # vl=0
    await check(dut, CORNERS[:VLMAX], CORNERS[2:2 + VLMAX], old, 5, 0b10101)
    dut._log.info("atum_vsmul: directed Q31 corners (incl -1*-1 saturate) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5217)
    for _ in range(6000):
        def rv():
            return rng.choice(CORNERS) if rng.random() < 0.4 else rng.getrandbits(32)
        vs1 = [rv() for _ in range(VLMAX)]
        vs2 = [rv() for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vsmul: 6000 random Q31 fractional multiplies match golden")
