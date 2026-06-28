"""cocotb testbench for atum_vmlogic — the AtumCore vector mask logical unit.

For each trial we randomise two VLMAX-bit masks, the op and VL, drive the
combinational mask-logic array, and compare the output mask against the golden
VectorUnit mask-logic methods (result bit set only for body-active lanes i < vl).
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8

OPS = {0: "vmand", 1: "vmor", 2: "vmxor", 3: "vmnand",
       4: "vmnor", 5: "vmxnor", 6: "vmandn", 7: "vmorn"}


def golden(op, m1_bits, m2_bits, vl):
    vu = g.VectorUnit()
    vu.vl = vl
    m1 = [(m1_bits >> i) & 1 for i in range(VLMAX)]
    m2 = [(m2_bits >> i) & 1 for i in range(VLMAX)]
    res = getattr(vu, OPS[op])(m1, m2)
    bits = 0
    for i in range(VLMAX):
        bits |= (int(res[i]) & 1) << i
    return bits


async def check(dut, op, m1_bits, m2_bits, vl):
    dut.m1.value = m1_bits
    dut.m2.value = m2_bits
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = int(dut.vd_mask.value)
    exp = golden(op, m1_bits, m2_bits, vl)
    assert got == exp, (
        f"op={OPS[op]} vl={vl} m1={m1_bits:08b} m2={m2_bits:08b}: "
        f"got {got:08b} != golden {exp:08b}")


@cocotb.test()
async def test_directed(dut):
    """Corners: all-zero / all-one masks, complementary masks, vl=0, partial vl."""
    pairs = [(0x00, 0x00), (0xFF, 0xFF), (0xFF, 0x00), (0xAA, 0x55),
             (0b10110010, 0b01101001)]
    for op in OPS:
        for m1, m2 in pairs:
            await check(dut, op, m1, m2, 8)
    # vl=0 -> all bits 0 for every op (incl the negating ops, whose body would be 1)
    for op in OPS:
        await check(dut, op, 0x00, 0x00, 0)
    # partial vl: tail bits must be 0 even where the op would produce 1
    await check(dut, 3, 0x00, 0x00, 4)   # vmnand body=1 -> low 4 bits set, rest 0
    await check(dut, 0, 0xFF, 0xFF, 5)   # vmand -> low 5 set
    dut._log.info("atum_vmlogic: directed mask-logic corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x10617)
    for _ in range(8000):
        op = rng.randint(0, 7)
        m1 = rng.getrandbits(VLMAX)
        m2 = rng.getrandbits(VLMAX)
        vl = rng.randint(0, VLMAX)
        await check(dut, op, m1, m2, vl)
    dut._log.info("atum_vmlogic: 8000 random mask-logic ops match golden")
