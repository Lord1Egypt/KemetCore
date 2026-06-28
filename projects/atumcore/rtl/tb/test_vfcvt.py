"""cocotb testbench for atum_vfcvt — the AtumCore int<->fp32 convert unit.

Drives a random vector, op (0..5), and VL, and compares every lane against the
golden VectorUnit.vfcvt (tail lanes 0). Covers both directions (int->fp RNE and
fp->int RNE/truncate, signed + unsigned) plus saturation corners (NaN, +/-Inf,
overflow, tiny/subnormal, the INT32_MIN / UINT32_MAX boundaries).
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

# op meaning: 0 f.x, 1 f.xu, 2 x.f, 3 xu.f, 4 rtz.x.f, 5 rtz.xu.f
I2F_OPS = (0, 1)
F2I_OPS = (2, 3, 4, 5)

# fp32 patterns that stress f->int saturation and rounding boundaries.
FP_SPECIALS = [
    0x00000000, 0x80000000,            # +0, -0
    0x3F000000, 0xBF000000,            # +0.5, -0.5  (ties -> even)
    0x3F800000, 0xBF800000,            # +1, -1
    0x40400000, 0xC0400000,            # +3, -3
    0x4F000000, 0xCF000000,            # +2**31, -2**31 (int32 boundary)
    0x4F7FFFFF, 0xCF7FFFFF,            # ~ just below 2**32
    0x4F800000,                        # 2**32 (uint32 overflow)
    0x7F800000, 0xFF800000,            # +Inf, -Inf
    0x7FC00000, 0x7F800001, 0xFFC00001,  # qNaN, sNaN, -NaN
    0x00000001, 0x80000001,            # +/- smallest subnormal
    0x33800000, 0x3E800000,            # tiny, 0.25 (-> 0)
    0x4EFFFFFF,                        # large positive
]

# integer patterns that stress int->fp rounding (>2**24 needs rounding).
INT_SPECIALS = [
    0x00000000, 0x00000001, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000,
    0x00FFFFFF, 0x01000000, 0x01000001, 0xFFFFFF00, 0x00FFFFFE,
    0x40000000, 0xC0000000, 0x0000FFFF, 0xABCDEF12, 0x12345678,
]


def fbits():
    return struct.unpack("<I", struct.pack("<f", random.uniform(-5e9, 5e9)))[0]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs, op, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    return [int(x) for x in vu.vfcvt(1, op)]


async def check(dut, vs, op, vl):
    vs = (list(vs) + [0] * VLMAX)[:VLMAX]
    dut.vs.value = pack(vs)
    dut.op.value = op
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs, op, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"op{op} lane{i} vl={vl} x={vs[i]:08x}: "
            f"got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """fp->int saturation/rounding corners + int->fp rounding corners + vl gating."""
    for op in F2I_OPS:
        await check(dut, FP_SPECIALS[:VLMAX], op, 8)
        await check(dut, FP_SPECIALS[8:8 + VLMAX], op, 8)
        await check(dut, FP_SPECIALS[16:16 + VLMAX], op, 8)
        await check(dut, FP_SPECIALS[:VLMAX], op, 3)        # tail -> 0
        await check(dut, FP_SPECIALS[:VLMAX], op, 0)
    for op in I2F_OPS:
        await check(dut, INT_SPECIALS[:VLMAX], op, 8)
        await check(dut, INT_SPECIALS[5:5 + VLMAX], op, 8)
        await check(dut, INT_SPECIALS[:VLMAX], op, 4)       # tail -> 0
    dut._log.info("atum_vfcvt: directed convert/saturate corners match golden")


@cocotb.test()
async def test_random_f2i(dut):
    rng = random.Random(0xFC71)
    random.seed(0xFC71)
    for _ in range(6000):
        vs = [rng.choice(FP_SPECIALS) if rng.random() < 0.4 else fbits()
              for _ in range(VLMAX)]
        op = rng.choice(F2I_OPS)
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, op, vl)
    dut._log.info("atum_vfcvt: 6000 random fp->int conversions match golden")


@cocotb.test()
async def test_random_i2f(dut):
    rng = random.Random(0x12F)
    for _ in range(6000):
        vs = [rng.choice(INT_SPECIALS) if rng.random() < 0.4
              else rng.randint(0, MASKW) for _ in range(VLMAX)]
        op = rng.choice(I2F_OPS)
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, op, vl)
    dut._log.info("atum_vfcvt: 6000 random int->fp conversions match golden")
