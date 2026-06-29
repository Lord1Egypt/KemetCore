"""cocotb testbench for atum_vfsqrt — the AtumCore fp32 vector square-root lane array.

Each trial randomises an fp32 source vector, the old destination, VL and the per-lane
mask, drives the combinational lane array, and compares every lane against the golden
VectorUnit. The lane datapath is HapiCore's correctly-rounded hapi_fp32_sqrt, so results
match numpy fp32 sqrt bit-for-bit (both round-to-nearest-even). Negative inputs and NaN
yield NaN (semantics equal, payload tolerated); +inf -> +inf; +/-0 -> +/-0.
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
            0x3F800000, 0xBF800000, 0x40000000, 0x40800000, 0x7F7FFFFF,
            0x7F800000, 0xFF800000, 0x7FC00000, 0x00800000, 0x4B000000]


def rand_bits(rng):
    if rng.random() < 0.35:
        return rng.choice(SPECIALS)
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-30, 30))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def golden(vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    vu.vfsqrt(3, 2, mask=mask)
    return [int(x) for x in vu.vreg[3].astype(np.uint32)]


async def check(dut, vs2, vd_old, vl, mask_bits):
    dut.vs2.value = pack(vs2)
    dut.vd_old.value = pack(vd_old)
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = unpack(dut.vd_new.value)
    exp = golden(vs2, vd_old, vl, mask_bits)
    for i in range(VLMAX):
        if is_nan(got[i]) and is_nan(exp[i]):
            continue  # both NaN: payload may differ, semantics equal
        assert got[i] == exp[i], (
            f"vfsqrt lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} (x={vs2[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    # corners: sqrt(0)=0, sqrt(1)=1, sqrt(4)=2, sqrt(neg)=nan, sqrt(inf)=inf, perfect+non
    x = [0x00000000, 0x3F800000, 0x40800000, 0xBF800000, 0x7F800000,
         0x40000000, 0x80000000, 0x41200000]   # 0,1,4,-1,inf,2,-0,10
    old = [0xA5A5A5A5] * VLMAX
    await check(dut, x, old, 8, 0xFF)        # full
    await check(dut, x, old, 0, 0xFF)        # vl=0: no writes
    await check(dut, x, old, 5, 0b00101)     # partial vl + sparse mask
    await check(dut, x, old, 8, 0b10101010)
    # perfect squares: sqrt(k*k) exact
    sq = [0x40800000, 0x41100000, 0x41C80000, 0x42480000,
          0x42C80000, 0x43160000, 0x43480000, 0x437A0000]  # 4,9,25,50,...
    await check(dut, sq, old, 8, 0xFF)
    dut._log.info("atum_vfsqrt: directed corners (0/1/4/neg/inf/perfect squares) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5A1207)
    for _ in range(5000):
        vs2 = [rand_bits(rng) for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, vs2, old, vl, mask)
    dut._log.info("atum_vfsqrt: 5000 random fp32 sqrts match golden (all vl/mask)")
