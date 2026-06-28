"""cocotb testbench for atum_vmfcmp — the AtumCore fp32 compare-to-mask unit.

For each trial we randomise two fp32 source vectors, the compare op, VL and the
per-lane input mask, drive the combinational comparator array, and compare the
VLMAX-bit output mask against the golden VectorUnit fp compare methods (which define
the active-element / tail policy + IEEE ordered/unordered semantics). fp32 elements
cross the boundary as raw bit patterns packed little-endian by lane.
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

OPS = {0: "vmfeq", 1: "vmfne", 2: "vmflt", 3: "vmfle", 4: "vmfgt", 5: "vmfge"}

# fp32 patterns stressing signs, zeros, Inf, NaN, subnormal, ordering boundaries.
SPECIALS = [0x00000000, 0x80000000,            # +0, -0  (compare equal)
            0x3F800000, 0xBF800000,            # +1, -1
            0x40000000, 0xC0000000,            # +2, -2
            0x00000001, 0x80000001,            # +/- smallest subnormal
            0x7F800000, 0xFF800000,            # +Inf, -Inf
            0x7FC00000, 0x7F800001,            # qNaN, sNaN
            0x7F7FFFFF, 0xFF7FFFFF, 0x40490FDB]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def rand_bits(rng):
    if rng.random() < 0.45:
        return rng.choice(SPECIALS)
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-30, 30))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def golden(op, vs1, vs2, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    res = getattr(vu, OPS[op])(1, 2, mask=mask)
    bits = 0
    for i in range(VLMAX):
        bits |= (int(res[i]) & 1) << i
    return bits


async def check(dut, op, vs1, vs2, vl, mask_bits):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.op.value = op
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = int(dut.vd_mask.value)
    exp = golden(op, vs1, vs2, vl, mask_bits)
    assert got == exp, (
        f"op={OPS[op]} vl={vl} mask={mask_bits:08b}: "
        f"got {got:08b} != golden {exp:08b} (a={[hex(x) for x in vs1]})")


@cocotb.test()
async def test_directed(dut):
    """IEEE corners: +0==-0, NaN unordered (only vmfne true), Inf ordering, sign
    boundary, vl=0, partial vl + sparse mask."""
    a = [0x00000000, 0x3F800000, 0xBF800000, 0x7F800000, 0x7FC00000,
         0x40000000, 0x80000000, 0x00000001]
    b = [0x80000000, 0x3F800000, 0x3F800000, 0xFF800000, 0x3F800000,
         0xC0000000, 0x00000000, 0x80000001]
    for op in OPS:
        await check(dut, op, a, b, 8, 0xFF)
    await check(dut, 0, a, b, 0, 0xFF)            # vl=0 -> all 0
    await check(dut, 2, a, b, 5, 0b10101)         # partial vl + sparse mask
    await check(dut, 3, a, b, 8, 0b11001100)
    # NaN on either side: vmfne all-1, every other op all-0 (within active lanes)
    nan = [0x7FC00000] * VLMAX
    num = [0x3F800000] * VLMAX
    await check(dut, 1, nan, num, 8, 0xFF)        # vmfne -> all 1
    await check(dut, 0, nan, num, 8, 0xFF)        # vmfeq -> all 0
    await check(dut, 3, nan, num, 8, 0xFF)        # vmfle -> all 0
    dut._log.info("atum_vmfcmp: directed fp compare corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xFCFC)
    for _ in range(6000):
        op = rng.randint(0, 5)
        vs1 = [rand_bits(rng) for _ in range(VLMAX)]
        # bias toward equal lanes so eq/le/ge fire often
        vs2 = [vs1[i] if rng.random() < 0.3 else rand_bits(rng)
               for i in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, vl, mask)
    dut._log.info("atum_vmfcmp: 6000 random fp compares match golden (all ops/vl/mask)")
