"""cocotb testbench for atum_viota — the AtumCore vector iota / index unit.

Drives a random source mask, v0.t input mask, op (viota/vid) and VL, and compares
every lane of the output vector against the golden VectorUnit.viota / vid (active
lanes get the prefix count or the index; inactive/tail lanes read 0).
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


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(op, m_bits, vmask_bits, vl):
    vu = g.VectorUnit()
    vu.vl = vl
    m = [(m_bits >> i) & 1 for i in range(VLMAX)]
    vmask = [(vmask_bits >> i) & 1 for i in range(VLMAX)]
    res = vu.vid(mask=vmask) if op else vu.viota(m, mask=vmask)
    return [int(x) for x in np.asarray(res, dtype=np.uint32)]


async def check(dut, op, m_bits, vmask_bits, vl):
    dut.m.value = m_bits
    dut.vmask.value = vmask_bits
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(op, m_bits, vmask_bits, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"op={'vid' if op else 'viota'} lane{i} vl={vl} m={m_bits:08b} "
            f"vmask={vmask_bits:08b}: got {got[i]} != golden {exp[i]}")


@cocotb.test()
async def test_directed(dut):
    """Corners: all-zero / all-one source mask, alternating, vl gating, v0.t
    masking (skipped lanes do not advance the iota count)."""
    for op in (0, 1):
        await check(dut, op, 0x00, 0xFF, 8)
        await check(dut, op, 0xFF, 0xFF, 8)
        await check(dut, op, 0b10110101, 0xFF, 8)
        await check(dut, op, 0xFF, 0xFF, 4)            # partial vl
        await check(dut, op, 0b11111111, 0b10101010, 8)  # sparse v0.t
    # viota specific: a masked-off (v0.t=0) lane must not advance the count
    await check(dut, 0, 0xFF, 0b11111101, 8)   # lane1 inactive -> its bit ignored
    dut._log.info("atum_viota: directed viota/vid corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x107A)
    for _ in range(8000):
        op = rng.randint(0, 1)
        m = rng.getrandbits(VLMAX)
        vmask = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, m, vmask, vl)
    dut._log.info("atum_viota: 8000 random viota/vid match golden")
