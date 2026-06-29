"""cocotb testbench for atum_vfdiv — the AtumCore fp32 vector divide lane array.

For each trial we randomise two fp32 source vectors, the old destination, the op
(vfdiv vs1/vs2 / vfrdiv vs2/vs1), VL and the per-lane mask, drive the combinational
lane array, and compare every lane against the golden VectorUnit. fp32 elements cross
the boundary as raw bit patterns packed little-endian by lane. The lane datapath is
HapiCore's correctly-rounded hapi_fp32_div, so results match numpy fp32 division
bit-for-bit (both round-to-nearest-even).
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
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-30, 30))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def golden(op, vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    (vu.vfrdiv if op else vu.vfdiv)(3, 1, 2, mask=mask)
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
    name = "vfrdiv" if op else "vfdiv"
    for i in range(VLMAX):
        if is_nan(got[i]) and is_nan(exp[i]):
            continue  # both NaN: payload may differ, semantics equal
        assert got[i] == exp[i], (
            f"{name} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} "
            f"(a={vs1[i]:08x} b={vs2[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    # corners: x/x=1, x/0=inf, 0/0=nan, inf/inf=nan, normal divides
    a = [0x3F800000, 0x40000000, 0x3F800000, 0x7F800000, 0x40490FDB,
         0x00800000, 0xC0000000, 0x4B000000]
    b = [0x3F800000, 0x40000000, 0x00000000, 0x7F800000, 0x40000000,
         0x40000000, 0x40000000, 0x40490FDB]
    old = [0xA5A5A5A5] * VLMAX
    for op in (0, 1):
        await check(dut, op, a, b, old, 8, 0xFF)       # full
        await check(dut, op, a, b, old, 0, 0xFF)       # vl=0: no writes
        await check(dut, op, a, b, old, 5, 0b00101)    # partial vl + sparse mask
        await check(dut, op, a, b, old, 8, 0b10101010)
    # self-divide: x / x == 1.0 for finite non-zero
    same = [0x40490FDB] * VLMAX
    await check(dut, 0, same, same, old, 8, 0xFF)
    dut._log.info("atum_vfdiv: directed fp corners (1.0/inf/nan/normal) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xD1F1DE)
    for _ in range(4000):
        op = rng.randint(0, 1)
        vs1 = [rand_bits(rng) for _ in range(VLMAX)]
        vs2 = [rand_bits(rng) for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vfdiv: 4000 random fp32 divides match golden (vfdiv/vfrdiv, all vl/mask)")
