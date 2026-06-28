"""cocotb testbench for atum_vmsbf — AtumCore mask set-before/including/only-first.

Drives a random mask, op (sbf/sif/sof) and VL, and compares the output mask against
the golden VectorUnit.vmsbf / vmsif / vmsof (relative to the first set bit; empty
source -> sbf/sif all-ones body, sof all-zero; tail 0).
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8
OPS = {0: "vmsbf", 1: "vmsif", 2: "vmsof"}


def golden(op, m_bits, vl):
    vu = g.VectorUnit()
    vu.vl = vl
    m = [(m_bits >> i) & 1 for i in range(VLMAX)]
    res = getattr(vu, OPS[op])(m)
    bits = 0
    for i in range(VLMAX):
        bits |= (int(res[i]) & 1) << i
    return bits


async def check(dut, op, m_bits, vl):
    dut.m.value = m_bits
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = int(dut.vd_mask.value)
    exp = golden(op, m_bits, vl)
    assert got == exp, (
        f"op={OPS[op]} vl={vl} m={m_bits:08b}: got {got:08b} != golden {exp:08b}")


@cocotb.test()
async def test_directed(dut):
    """Corners: empty mask, single bit, first-at-0, first-at-last, vl gating."""
    for op in (0, 1, 2):
        await check(dut, op, 0x00, 8)        # empty -> sbf/sif all-1, sof all-0
        await check(dut, op, 0x01, 8)        # first at lane 0
        await check(dut, op, 0x80, 8)        # first at lane 7
        await check(dut, op, 0b00101000, 8)  # first set bit = lane 3
        await check(dut, op, 0xFF, 8)        # first at 0
        await check(dut, op, 0b00100000, 3)  # the set bit is beyond vl -> empty body
        await check(dut, op, 0b00000100, 5)  # first at 2, partial vl
    dut._log.info("atum_vmsbf: directed mask set-first corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5B1F)
    for _ in range(8000):
        op = rng.randint(0, 2)
        m = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, m, vl)
    dut._log.info("atum_vmsbf: 8000 random mask set-first ops match golden")
