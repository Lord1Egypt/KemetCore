"""cocotb testbench for atum_vimac — the AtumCore integer multiply-add family.

Each trial randomises vs1, vs2, the destination vd_old (which is a multiply-add
operand), the op (vmacc/vnmsac/vmadd/vnmsub), VL and the per-lane mask, drives the
combinational lane array, and compares every lane against the golden VectorUnit
(modular 2^32 multiply-add). Operands cross the boundary packed little-endian by lane.
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

OPS = {0: "vmacc", 1: "vnmsac", 2: "vmadd", 3: "vnmsub"}

CORNERS = [0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 2, 0x12345678, 0xDEADBEEF]


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(op, vs1, vs2, vd_old, vl, mask_bits):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs1, dtype=np.uint32)
    vu.vreg[2] = np.array(vs2, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    mask = [bool((mask_bits >> i) & 1) for i in range(VLMAX)]
    getattr(vu, OPS[op])(3, 1, 2, mask=mask)
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
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"{OPS[op]} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x} "
            f"(s1={vs1[i]:08x} s2={vs2[i]:08x} d={vd_old[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    a = CORNERS[:VLMAX]
    b = CORNERS[2:2 + VLMAX] if len(CORNERS) >= 2 + VLMAX else (CORNERS + CORNERS)[2:2 + VLMAX]
    d = [0x00000003, 0xFFFFFFFF, 0x10000000, 1, 0x80000000, 7, 0xABCD, 0x55555555]
    for op in OPS:
        await check(dut, op, a, b, d, 8, 0xFF)
        await check(dut, op, a, b, d, 0, 0xFF)            # vl=0: undisturbed
        await check(dut, op, a, b, d, 5, 0b10101)         # partial vl + sparse mask
        await check(dut, op, a, b, d, 8, 0b01101001)
    dut._log.info("atum_vimac: directed integer multiply-add corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x1AC0)
    for _ in range(6000):
        op = rng.randint(0, 3)

        def rv():
            return rng.choice(CORNERS) if rng.random() < 0.35 else rng.getrandbits(32)
        vs1 = [rv() for _ in range(VLMAX)]
        vs2 = [rv() for _ in range(VLMAX)]
        old = [rv() for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vimac: 6000 random integer multiply-adds match golden (all ops/vl/mask)")
