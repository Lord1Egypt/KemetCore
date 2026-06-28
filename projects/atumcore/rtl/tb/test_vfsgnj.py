"""cocotb testbench for atum_vfsgnj — the AtumCore fp sign-injection unit.

Drives two random fp32 source vectors, op (sgnj/sgnjn/sgnjx) and VL, and compares
every lane of the result against the golden VectorUnit.vfsgnj (magnitude from vs1,
sign chosen by op; tail lanes 0).
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


def golden(vs1, vs2, op, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vl = vl
    return [int(x) for x in vu.vfsgnj(1, 2, op)]


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
            f"op={op} lane{i} vl={vl}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """fp corners: +/-0, +/-1, +/-inf, a NaN, mixed signs; all three ops, vl gating."""
    a = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000,
         0x7F800000, 0xFF800000, 0x7FC00000, 0x40490FDB]   # 0,-0,1,-1,inf,-inf,nan,pi
    b = [0x80000000, 0x00000000, 0xBF800000, 0x3F800000,
         0xFF800000, 0x7F800000, 0x80000000, 0xC0000000]
    for op in (0, 1, 2):
        await check(dut, a, b, op, 8)
        await check(dut, a, b, op, 4)        # vl gating
    # negate (sgnjn with vs2==vs1) flips sign; abs (sgnjx with vs2==vs1) clears sign
    await check(dut, a, a, 1, 8)             # -> negate each
    await check(dut, a, a, 2, 8)             # -> abs each (sign = x^x = 0)
    dut._log.info("atum_vfsgnj: directed fp sign corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x519A1)
    for _ in range(8000):
        a = [rng.getrandbits(32) for _ in range(VLMAX)]
        b = [rng.getrandbits(32) for _ in range(VLMAX)]
        op = rng.randint(0, 2)
        vl = rng.randint(0, VLMAX)
        await check(dut, a, b, op, vl)
    dut._log.info("atum_vfsgnj: 8000 random sign injections match golden")
