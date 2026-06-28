"""cocotb testbench for atum_vredu — the AtumCore vector reduction unit.

Drives random vectors / VL / mask and compares the scalar reduction (vredsum or
vredmax) against the golden VectorUnit. vredmax requires at least one active lane
(the golden max() of an empty selection is undefined), so those trials are
constructed to always keep a lane active.
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


def active_lanes(vl, mask_bits):
    return [i for i in range(VLMAX) if i < vl and ((mask_bits >> i) & 1)]


def golden(redop, vs, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    fn = {0: vu.vredsum, 1: vu.vredmax, 2: vu.vredand, 3: vu.vredor, 4: vu.vredxor}[redop]
    return int(fn(1, mask=mask)) & MASKW


async def check(dut, redop, vs, vl, mask_bits):
    dut.vs.value = pack(vs)
    dut.vl.value = vl
    dut.mask.value = mask_bits
    dut.redop.value = redop
    await Timer(1, units="ns")
    got = int(dut.result.value)
    exp = golden(redop, vs, vl, mask_bits)
    kind = {0: "sum", 1: "max", 2: "and", 3: "or", 4: "xor"}[redop]
    assert got == exp, (f"vred{kind} vl={vl} mask={mask_bits:08b}: "
                        f"got {got:08x} != golden {exp:08x}")


@cocotb.test()
async def test_directed(dut):
    a = [0x00000001, 0x00000002, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000,
         0x00000000, 0x12345678, 0x0000000A]
    # sum, full mask, full vl (overflow past 32 bits wraps)
    await check(dut, 0, a, 8, 0xFF)
    # sum, vl=0 -> empty sum is 0
    await check(dut, 0, a, 0, 0xFF)
    # sum, sparse mask
    await check(dut, 0, a, 8, 0b01010101)
    # max, full (unsigned max -> 0xFFFFFFFF)
    await check(dut, 1, a, 8, 0xFF)
    # max, restricted to lanes whose max is 0x7FFFFFFF
    await check(dut, 1, a, 4, 0b1111)
    # max, single active lane
    await check(dut, 1, a, 8, 0b00010000)
    # and/or/xor reductions, full + sparse
    for rop in (2, 3, 4):
        await check(dut, rop, a, 8, 0xFF)
        await check(dut, rop, a, 5, 0b10110)
        await check(dut, rop, a, 0, 0xFF)     # empty: and->all1, or/xor->0
    dut._log.info("atum_vredu: directed reductions (sum/max/and/or/xor) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5EED5)
    for _ in range(6000):
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        # sum/and/or/xor: any vl/mask (empty handled by identities)
        for rop in (0, 2, 3, 4):
            await check(dut, rop, vs, vl, mask)
        # max: ensure >= 1 active lane
        vlm, mm = vl, mask
        if not active_lanes(vlm, mm):
            vlm = rng.randint(1, VLMAX)
            mm = mask | 1
        await check(dut, 1, vs, vlm, mm)
    dut._log.info("atum_vredu: 6000 random reductions (sum/max/and/or/xor) match golden")
