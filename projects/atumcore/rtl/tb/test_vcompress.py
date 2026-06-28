"""cocotb testbench for atum_vcompress — the AtumCore vector compress unit.

Drives a random source vector, compress mask and VL, and compares every lane of
the packed result against the golden VectorUnit.vcompress (kept elements packed to
the low lanes in order; remaining high lanes read 0).
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


def golden(vs, m_bits, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    m = [(m_bits >> i) & 1 for i in range(VLMAX)]
    return [int(x) for x in vu.vcompress(1, m)]


async def check(dut, vs, m_bits, vl):
    dut.vs.value = pack(vs)
    dut.m.value = m_bits
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs, m_bits, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"lane{i} vl={vl} m={m_bits:08b}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """Corners: keep none / keep all / alternating, vl gating, single kept lane."""
    vs = [0x11111111, 0x22222222, 0x33333333, 0x44444444,
          0x55555555, 0x66666666, 0x77777777, 0x88888888]
    await check(dut, vs, 0x00, 8)        # keep none -> all zero
    await check(dut, vs, 0xFF, 8)        # keep all  -> unchanged
    await check(dut, vs, 0b10101010, 8)  # keep odd lanes -> packed front
    await check(dut, vs, 0b00010000, 8)  # single kept lane (lane4) -> lane0
    await check(dut, vs, 0xFF, 4)        # vl=4: only first 4 considered
    await check(dut, vs, 0b11110000, 4)  # mask bits beyond vl ignored -> empty
    dut._log.info("atum_vcompress: directed corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0117E)
    for _ in range(8000):
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        m = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, m, vl)
    dut._log.info("atum_vcompress: 8000 random compress ops match golden")
