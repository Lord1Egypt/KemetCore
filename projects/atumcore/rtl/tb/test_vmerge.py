"""cocotb testbench for atum_vmerge — the AtumCore vector merge / select unit.

Drives two random source vectors, a select mask and VL, and compares every lane of
the merged result against the golden VectorUnit.vmerge (vd[i] = m[i]?vs1[i]:vs2[i]
for i<vl, tail 0).
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


def golden(vs1, vs2, m_bits, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vl = vl
    m = [(m_bits >> i) & 1 for i in range(VLMAX)]
    return [int(x) for x in vu.vmerge(1, 2, m)]


async def check(dut, vs1, vs2, m_bits, vl):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.m.value = m_bits
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs1, vs2, m_bits, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"lane{i} vl={vl} m={m_bits:08b}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """Corners: all-from-vs1, all-from-vs2, alternating, vl gating."""
    a = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7]
    b = [0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7]
    await check(dut, a, b, 0xFF, 8)        # all vs1
    await check(dut, a, b, 0x00, 8)        # all vs2
    await check(dut, a, b, 0b10101010, 8)  # alternating
    await check(dut, a, b, 0xFF, 4)        # vl=4: tail 0
    await check(dut, a, b, 0b11110000, 6)  # mix + partial vl
    dut._log.info("atum_vmerge: directed merge corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x6E6E)
    for _ in range(8000):
        a = [rng.getrandbits(32) for _ in range(VLMAX)]
        b = [rng.getrandbits(32) for _ in range(VLMAX)]
        m = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, a, b, m, vl)
    dut._log.info("atum_vmerge: 8000 random merges match golden")
