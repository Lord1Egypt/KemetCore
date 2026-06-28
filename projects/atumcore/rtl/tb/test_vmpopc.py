"""cocotb testbench for atum_vmpopc — the AtumCore vector mask reduction unit.

Drives a random mask, v0.t input mask, op (vcpop/vfirst) and VL, and compares the
scalar result against the golden VectorUnit.vcpop / vfirst (only body-active and
v0.t-active lanes contribute; vfirst returns -1 when none are set).
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8


def golden(op, m_bits, vmask_bits, vl):
    vu = g.VectorUnit()
    vu.vl = vl
    m = [(m_bits >> i) & 1 for i in range(VLMAX)]
    vmask = [(vmask_bits >> i) & 1 for i in range(VLMAX)]
    if op == 0:
        return vu.vcpop(m, mask=vmask)
    return vu.vfirst(m, mask=vmask)


async def check(dut, op, m_bits, vmask_bits, vl):
    dut.m.value = m_bits
    dut.vmask.value = vmask_bits
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = dut.result.value.signed_integer
    exp = golden(op, m_bits, vmask_bits, vl)
    assert got == exp, (
        f"op={'vfirst' if op else 'vcpop'} vl={vl} m={m_bits:08b} "
        f"vmask={vmask_bits:08b}: got {got} != golden {exp}")


@cocotb.test()
async def test_directed(dut):
    """Corners: empty mask (vcpop=0, vfirst=-1), full mask, single bit, vl gating,
    v0.t masking off the only set bit."""
    for op in (0, 1):
        await check(dut, op, 0x00, 0xFF, 8)   # none set
        await check(dut, op, 0xFF, 0xFF, 8)   # all set
        await check(dut, op, 0x80, 0xFF, 8)   # only top lane
        await check(dut, op, 0x01, 0xFF, 8)   # only lane0
        await check(dut, op, 0x10, 0xFF, 3)   # set bit beyond vl -> not counted
        await check(dut, op, 0x04, 0b11111011, 8)  # the only set lane is masked off
        await check(dut, op, 0xAA, 0xFF, 5)   # partial vl
    dut._log.info("atum_vmpopc: directed vcpop/vfirst corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0FFEE)
    for _ in range(8000):
        op = rng.randint(0, 1)
        m = rng.getrandbits(VLMAX)
        vmask = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, m, vmask, vl)
    dut._log.info("atum_vmpopc: 8000 random vcpop/vfirst match golden")
