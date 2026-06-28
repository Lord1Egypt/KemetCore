"""cocotb testbench for atum_vsadd — the AtumCore saturating add/sub unit.

For each trial we randomise the two source vectors, the op (vsaddu/vsadd/vssubu/
vssub), VL and the per-lane mask, drive the combinational lane array, and compare
every lane against the golden VectorUnit saturating methods (which define both the
clamp behaviour and the active-element / tail policy). Operands cross the boundary
packed little-endian by lane: element i at bits [i*32 +: 32].
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

OPS = {0: "vsaddu", 1: "vsadd", 2: "vssubu", 3: "vssub"}

# values that hit the saturation boundaries hard
CORNERS = [0, 1, 2, 0x7FFFFFFF, 0x80000000, 0x80000001, 0xFFFFFFFF,
           0x7FFFFFFE, 0x40000000, 0xC0000000]


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
            f"got {got[i]:08x} != golden {exp[i]:08x} (a={vs1[i]:08x} b={vs2[i]:08x})")


@cocotb.test()
async def test_directed(dut):
    """Saturation corners: +overflow, -overflow, unsigned wrap, underflow-to-0,
    vl gating, sparse mask."""
    old = [0x5A5A5A5A] * VLMAX
    a = CORNERS[:VLMAX]
    b = CORNERS[2:2 + VLMAX]
    for op in OPS:
        await check(dut, op, a, b, old, 8, 0xFF)
        await check(dut, op, a, b, old, 0, 0xFF)          # vl=0: undisturbed
        await check(dut, op, a, b, old, 5, 0b10101)       # partial vl + sparse mask
    # explicit boundary cases
    await check(dut, 0, [0xFFFFFFFF] * VLMAX, [1] * VLMAX, old, 8, 0xFF)  # vsaddu -> UMAX
    await check(dut, 1, [0x7FFFFFFF] * VLMAX, [1] * VLMAX, old, 8, 0xFF)  # vsadd  -> SMAX
    await check(dut, 1, [0x80000000] * VLMAX, [0xFFFFFFFF] * VLMAX, old, 8, 0xFF)  # -> SMIN
    await check(dut, 2, [1] * VLMAX, [2] * VLMAX, old, 8, 0xFF)           # vssubu -> 0
    await check(dut, 3, [0x80000000] * VLMAX, [1] * VLMAX, old, 8, 0xFF)  # vssub  -> SMIN
    dut._log.info("atum_vsadd: directed saturation corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5A77)
    for _ in range(6000):
        op = rng.randint(0, 3)

        def rv():
            return rng.choice(CORNERS) if rng.random() < 0.5 else rng.getrandbits(32)
        vs1 = [rv() for _ in range(VLMAX)]
        vs2 = [rv() for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        mask = rng.getrandbits(VLMAX)
        await check(dut, op, vs1, vs2, old, vl, mask)
    dut._log.info("atum_vsadd: 6000 random saturating ops match golden (all ops/vl/mask)")
