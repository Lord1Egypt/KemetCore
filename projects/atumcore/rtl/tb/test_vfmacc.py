"""cocotb testbench for atum_vfmacc — the AtumCore fp32 fused multiply-add lanes.

Each trial randomises two fp32 sources, the destination accumulator (vd_old, which
is also the FMA's third operand), the op (vfmacc +acc / vfmsac -acc), VL and the
per-lane mask, drives the combinational lane array, and compares every lane against
the golden VectorUnit (single-rounded FMA via the shared HapiCore fp_fma). fp32
elements cross the boundary as raw bit patterns packed little-endian by lane.
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


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def is_nan(bits):
    return (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF) != 0


SPECIALS = [0x00000000, 0x80000000, 0x00000001, 0x80000001, 0x007FFFFF,
            0x3F800000, 0xBF800000, 0x40490FDB, 0x7F7FFFFF, 0xFF7FFFFF,
            0x7F800000, 0xFF800000, 0x7FC00000, 0x00800000, 0x4B000000]


def rand_bits(rng):
    if rng.random() < 0.35:
        return rng.choice(SPECIALS)
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-20, 20))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def golden(op, vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    (vu.vfmacc, vu.vfmsac, vu.vfnmacc, vu.vfnmsac)[op](3, 1, 2, mask=mask)
    return [int(x) for x in vu.vreg[3].astype(np.uint32)]


async def check(dut, op, vs1, vs2, vd_old, vl, mask_bits):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.vd_old.value = pack(vd_old)
    dut.op.value = op
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = unpack(dut.vd_new.value)
    exp = golden(op, vs1, vs2, vd_old, vl, mask_bits)
    name = ("vfmacc", "vfmsac", "vfnmacc", "vfnmsac")[op]
    for i in range(VLMAX):
        if is_nan(got[i]) and is_nan(exp[i]):
            continue
        assert got[i] == exp[i], (
            f"{name} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} "
            f"(a={vs1[i]:08x} b={vs2[i]:08x} c={vd_old[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    a = [0x3F800000, 0x40000000, 0x80000000, 0x00000000, 0x7F800000,
         0x00800000, 0xBF800000, 0x40490FDB]
    b = [0x3F800000, 0x3F000000, 0x40000000, 0x80000000, 0x3F800000,
         0x00800000, 0x40490FDB, 0x3F800000]
    c = [0x3F000000, 0x40400000, 0x3F800000, 0x3F800000, 0xFF800000,
         0x00000001, 0x40000000, 0xBF800000]
    for op in (0, 1, 2, 3):
        await check(dut, op, a, b, c, 8, 0xFF)         # full
        await check(dut, op, a, b, c, 0, 0xFF)         # vl=0: accumulator untouched
        await check(dut, op, a, b, c, 5, 0b00101)      # partial vl + sparse mask
        await check(dut, op, a, b, c, 8, 0b10101010)
    dut._log.info("atum_vfmacc: directed fma family corners (zeros/inf/nan/cancel) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xFADDED)
    for _ in range(4000):
        op = rng.randint(0, 3)
        vs1 = [rand_bits(rng) for _ in range(VLMAX)]
        vs2 = [rand_bits(rng) for _ in range(VLMAX)]
        old = [rand_bits(rng) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vfmacc: 4000 random fp32 FMAs match golden (macc/msac/nmacc/nmsac, all vl/mask)")
