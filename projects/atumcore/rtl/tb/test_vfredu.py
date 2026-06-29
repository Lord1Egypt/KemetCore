"""cocotb testbench for atum_vfredu — the AtumCore fp32 vector sum reduction.

Each trial randomises an fp32 source vector, VL and the per-lane mask, drives the
combinational adder chain, and compares the scalar result against the golden VectorUnit
(sequential left-to-right np.float32 accumulation). fp32 elements cross the boundary as
raw bit patterns packed little-endian by lane; the result is a single fp32 bit pattern.
The lane datapath is HapiCore's correctly-rounded hapi_fp32_add, so the chained sum is
bit-exact with the golden's ordered accumulation.
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


def golden(vs, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[2] = np.array(vs, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    return vu.vfredosum(2, mask=mask)


async def check(dut, vs, vl, mask_bits):
    dut.vs.value = pack(vs)
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = int(dut.result.value)
    exp = golden(vs, vl, mask_bits)
    if is_nan(got) and is_nan(exp):
        return  # both NaN: payload may differ, semantics equal
    assert got == exp, (
        f"vfredu vl={vl} mask={mask_bits:08b}: got {got:08x} != golden {exp:08x} "
        f"(vs={[f'{x:08x}' for x in vs]})")


@cocotb.test()
async def test_directed(dut):
    one = 0x3F800000
    two = 0x40000000
    await check(dut, [one] * VLMAX, 8, 0xFF)        # 1*8 = 8.0
    await check(dut, [one] * VLMAX, 0, 0xFF)        # vl=0 -> +0.0
    await check(dut, [one] * VLMAX, 4, 0xFF)        # 1*4 = 4.0
    await check(dut, [two] * VLMAX, 8, 0b10101010)  # only 4 active -> 8.0
    # cancellation: +x and -x sum to +0.0
    pm = [one, 0xBF800000, two, 0xC0000000, 0x40490FDB, 0xC0490FDB, one, 0xBF800000]
    await check(dut, pm, 8, 0xFF)
    # inf + finite = inf
    await check(dut, [0x7F800000, one, two, one, two, one, two, one], 8, 0xFF)
    dut._log.info("atum_vfredu: directed fp sum corners (powers/cancel/inf) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xFEED5)
    for _ in range(6000):
        vs = [rand_bits(rng) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, vs, vl, mask)
    dut._log.info("atum_vfredu: 6000 random fp32 sum reductions match golden (all vl/mask)")
