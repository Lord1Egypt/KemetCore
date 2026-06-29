"""cocotb testbench for atum_vfredminmax — AtumCore fp32 min/max reduction.

Each trial randomises an fp32 source vector, op (min/max), VL and the per-lane mask,
drives the combinational fold chain, and compares the scalar result against the golden
VectorUnit (identity-seeded left-to-right fold with monotonic-key + NaN-skip semantics).
"""
import os
import random
import struct
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


def is_nan(bits):
    return (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF) != 0


SPECIALS = [0x00000000, 0x80000000, 0x00000001, 0x80000001, 0x007FFFFF,
            0x3F800000, 0xBF800000, 0x40490FDB, 0x7F7FFFFF, 0xFF7FFFFF,
            0x7F800000, 0xFF800000, 0x7FC00000, 0x00800000, 0x4B000000]


def rand_bits(rng):
    if rng.random() < 0.30:
        return rng.choice(SPECIALS)
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-20, 20))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def golden(op, vs, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[2] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    return (vu.vfredmax if op else vu.vfredmin)(2, mask=mask)


async def check(dut, op, vs, vl, mask_bits):
    dut.vs.value = pack(vs)
    dut.op.value = op
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = int(dut.result.value)
    exp = golden(op, vs, vl, mask_bits)
    if is_nan(got) and is_nan(exp):
        return
    name = "vfredmax" if op else "vfredmin"
    assert got == exp, (
        f"{name} vl={vl} mask={mask_bits:08b}: got {got:08x} != golden {exp:08x} "
        f"(vs={[f'{x:08x}' for x in vs]})")


@cocotb.test()
async def test_directed(dut):
    vals = [0x3F800000, 0x40000000, 0xBF800000, 0x40490FDB,
            0x00000000, 0x80000000, 0x41200000, 0xC1200000]  # 1,2,-1,pi,+0,-0,10,-10
    for op in (0, 1):
        await check(dut, op, vals, 8, 0xFF)
        await check(dut, op, vals, 0, 0xFF)          # empty -> identity
        await check(dut, op, vals, 5, 0b00101)
        await check(dut, op, vals, 8, 0b10101010)
    # signed zero: min should give -0, max +0
    await check(dut, 0, [0x00000000, 0x80000000] + [0x7F800000] * 6, 8, 0xFF)
    await check(dut, 1, [0x00000000, 0x80000000] + [0xFF800000] * 6, 8, 0xFF)
    # NaN skipped among numbers; inf extremes
    nanmix = [0x7FC00000, 0x40000000, 0x7F800000, 0xFF800000,
              0x3F800000, 0x7FC00000, 0xC0000000, 0x40490FDB]
    await check(dut, 0, nanmix, 8, 0xFF)
    await check(dut, 1, nanmix, 8, 0xFF)
    dut._log.info("atum_vfredminmax: directed (signed-zero/NaN/inf/empty) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x1DEA77)
    for _ in range(6000):
        op = rng.randint(0, 1)
        vs = [rand_bits(rng) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs, vl, mask)
    dut._log.info("atum_vfredminmax: 6000 random fp32 min/max reductions match golden")
