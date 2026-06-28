"""cocotb testbench for atum_vmask — the AtumCore vector compare-to-mask unit.

For each trial we randomise the two source vectors, the compare op, VL and the
per-lane input mask, drive the combinational comparator array, and compare the
VLMAX-bit output mask against the golden VectorUnit compare methods (which define
the active-element / tail policy: an output bit is set only for a body-active,
mask-active lane whose comparison holds). Operands cross the boundary packed
little-endian by lane: element i at bits [i*32 +: 32].
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

OPS = {0: "vmseq", 1: "vmsne", 2: "vmsltu", 3: "vmslt", 4: "vmsleu", 5: "vmsle"}


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


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
        f"got {got:08b} != golden {exp:08b}")


@cocotb.test()
async def test_directed(dut):
    """Corners: equal lanes, signed vs unsigned ordering across the sign boundary,
    vl=0 (all bits 0), partial vl, sparse mask."""
    # mix of equal, signed-negative (>=0x80000000) and positive operands
    a = [0x00000001, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0, 0x12345678, 0xDEADBEEF, 5]
    b = [0x00000001, 0x00000001, 0x80000000, 0x7FFFFFFF, 1, 0x12345679, 0x0000BEEF, 5]
    for op in OPS:
        await check(dut, op, a, b, 8, 0xFF)
    # vl=0 -> output all zero regardless of compares/mask
    await check(dut, 0, a, b, 0, 0xFF)
    # partial vl + sparse mask
    await check(dut, 2, a, b, 5, 0b10101)
    await check(dut, 3, a, b, 8, 0b11001100)
    # signed vs unsigned distinction: 0x80000000 < 1 unsigned-false, signed-true
    sa = [0x80000000] * VLMAX
    sb = [0x00000001] * VLMAX
    await check(dut, 2, sa, sb, 8, 0xFF)   # vmsltu -> all 0
    await check(dut, 3, sa, sb, 8, 0xFF)   # vmslt  -> all 1
    dut._log.info("atum_vmask: directed compare corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5EED)
    for _ in range(6000):
        op = rng.randint(0, 5)
        # bias toward collisions so == / <= fire often
        def rv():
            return rng.choice([0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF,
                               rng.getrandbits(32)])
        vs1 = [rv() for _ in range(VLMAX)]
        vs2 = [rv() for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, vl, mask)
    dut._log.info("atum_vmask: 6000 random compares match golden (all ops/vl/mask)")
