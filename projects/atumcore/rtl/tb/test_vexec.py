"""cocotb testbench for atum_vexec — the AtumCore vector execute unit.

Drives a stream of mixed operations (integer ALU incl vmacc, fp32 vfadd/vfmul, and
reductions) through the integrated unit and checks the vector output against the
golden VectorUnit, validating the decode/mux wiring on top of the already-verified
sub-blocks. For a reduction the scalar must land in element 0 with elements 1.. kept
from vd_old.
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

ALU_OPS = {0: "vadd", 1: "vsub", 2: "vmul", 3: "vand", 4: "vor",
           5: "vxor", 6: "vsll", 7: "vsrl", 8: "vmacc"}
SPECIALS = [0x00000000, 0x80000000, 0x00000001, 0x3F800000, 0xBF800000,
            0x40490FDB, 0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000, 0x00800000]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def is_nan(bits):
    return (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF) != 0


def rand_fbits(rng):
    if rng.random() < 0.35:
        return rng.choice(SPECIALS)
    m = rng.uniform(-1, 1) * (2.0 ** rng.randint(-30, 30))
    return struct.unpack("<I", struct.pack("<f", m))[0]


def active_lanes(vl, mask_bits):
    return [i for i in range(VLMAX) if i < vl and ((mask_bits >> i) & 1)]


def golden_vec(vclass, subop, vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    if vclass == 0:
        getattr(vu, ALU_OPS[subop])(3, 1, 2, mask=mask)
        return [int(x) for x in vu.vreg[3].astype(np.uint32)]
    if vclass == 1:
        (vu.vfmul if (subop & 1) else vu.vfadd)(3, 1, 2, mask=mask)
        return [int(x) for x in vu.vreg[3].astype(np.uint32)]
    # reduction: scalar into lane 0, rest keep vd_old
    scalar = int(vu.vredmax(1, mask=mask) if (subop & 1) else vu.vredsum(1, mask=mask)) & MASKW
    return [scalar] + [int(x) for x in vd_old[1:]]


async def check(dut, vclass, subop, vs1, vs2, vd_old, vl, mask_bits):
    dut.vs1.value = pack(vs1)
    dut.vs2.value = pack(vs2)
    dut.vd_old.value = pack(vd_old)
    dut.vclass.value = vclass
    dut.subop.value = subop
    dut.vl.value = vl
    dut.mask.value = mask_bits
    await Timer(1, units="ns")
    got = unpack(dut.vd_new.value)
    exp = golden_vec(vclass, subop, vs1, vs2, vd_old, vl, mask_bits)
    for i in range(VLMAX):
        if vclass == 1 and is_nan(got[i]) and is_nan(exp[i]):
            continue
        assert got[i] == exp[i], (
            f"vclass={vclass} subop={subop} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    ai = [1, 2, 0xFFFFFFFF, 0x7FFFFFFF, 5, 0, 0x10, 3]
    bi = [1, 3, 1, 2, 99, 7, 4, 0x40000000]
    af = [0x3F800000, 0x40000000, 0x80000000, 0x00000000, 0x7F800000, 0x00800000, 0xBF800000, 0x3F800000]
    bf = [0x3F800000, 0x3F000000, 0x00000000, 0x80000000, 0x3F800000, 0x00800000, 0x40490FDB, 0x40000000]
    old = [0xA5A5A5A5] * VLMAX
    for op in ALU_OPS:                          # every integer op incl vmacc
        await check(dut, 0, op, ai, bi, old, 8, 0xFF)
    await check(dut, 1, 0, af, bf, old, 8, 0xFF)   # vfadd
    await check(dut, 1, 1, af, bf, old, 8, 0xFF)   # vfmul
    await check(dut, 2, 0, ai, bi, old, 8, 0xFF)   # vredsum
    await check(dut, 2, 1, ai, bi, old, 8, 0xFF)   # vredmax
    await check(dut, 2, 0, ai, bi, old, 0, 0xFF)   # vredsum empty -> 0 in lane0
    dut._log.info("atum_vexec: directed mixed ops match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5EC0DE)
    for _ in range(6000):
        vclass = rng.randint(0, 2)
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        if vclass == 1:
            subop = rng.randint(0, 1)
            vs1 = [rand_fbits(rng) for _ in range(VLMAX)]
            vs2 = [rand_fbits(rng) for _ in range(VLMAX)]
        elif vclass == 2:
            subop = rng.randint(0, 1)
            vs1 = [rng.getrandbits(32) for _ in range(VLMAX)]
            vs2 = [rng.getrandbits(32) for _ in range(VLMAX)]
            if subop == 1 and not active_lanes(vl, mask):   # vredmax needs an active lane
                vl = rng.randint(1, VLMAX)
                mask |= 1
        else:
            subop = rng.randint(0, 8)
            vs1 = [rng.getrandbits(32) for _ in range(VLMAX)]
            vs2 = [rng.getrandbits(32) for _ in range(VLMAX)]
        await check(dut, vclass, subop, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vexec: 6000 random mixed ops (ALU/FP/RED) match golden")
