"""cocotb testbench for atum_valu — the AtumCore vector integer ALU lane array.

For each trial we randomise the two source vectors, the old destination vector, the
op, VL and the per-lane mask, drive the combinational lane array, and compare every
lane of the result against the golden VectorUnit (which defines the active-element /
undisturbed-tail write semantics). Operands cross the boundary packed little-endian
by lane: element i at bits [i*32 +: 32].
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

OPS = {0: "vadd", 1: "vsub", 2: "vmul", 3: "vand",
       4: "vor", 5: "vxor", 6: "vsll", 7: "vsrl", 8: "vmacc"}


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
            f"op={OPS[op]} lane{i} vl={vl} mask={mask_bits:08b}: "
            f"got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """Hand-picked corners: full vl/mask, vl=0 (no writes), single active lane,
    shift-by-large, multiply overflow, subtract underflow."""
    a = [0x00000001, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0, 0x12345678, 0xDEADBEEF, 3]
    b = [0x00000001, 0x00000001, 0x00000002, 1, 99, 0xFF, 17, 0x40000000]
    old = [0xA5A5A5A5] * VLMAX
    # vl=8, full mask: every op
    for op in OPS:
        await check(dut, op, a, b, old, 8, 0xFF)
    # vl=0: nothing writes regardless of mask
    await check(dut, 0, a, b, old, 0, 0xFF)
    # partial vl + sparse mask
    await check(dut, 2, a, b, old, 5, 0b00101)
    await check(dut, 1, a, b, old, 8, 0b10101010)
    # shift amounts > 31 must wrap to b[4:0]
    sh = [33, 64, 31, 1, 0, 7, 32, 5]
    await check(dut, 6, a, sh, old, 8, 0xFF)
    await check(dut, 7, a, sh, old, 8, 0xFF)
    # vmacc: vd += vs1*vs2 (low 32), incl product overflow + partial vl/mask
    macc_old = [0x100, 0xFFFFFF00, 1, 0, 0x7FFFFFFF, 0xDEAD, 42, 0x80000000]
    await check(dut, 8, a, b, macc_old, 8, 0xFF)
    await check(dut, 8, a, b, macc_old, 5, 0b10110)
    dut._log.info("atum_valu: directed corners (incl vmacc) match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xA70BEEF)
    for _ in range(6000):
        op = rng.randint(0, 8)
        vs1 = [rng.getrandbits(32) for _ in range(VLMAX)]
        vs2 = [rng.getrandbits(32) for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_valu: 6000 random vector ops (incl vmacc) match golden (all ops/vl/mask)")
