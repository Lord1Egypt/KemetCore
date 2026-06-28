"""cocotb testbench for atum_vrgather — the AtumCore vector register gather unit.

Drives a random source vector, index vector and VL, and compares every lane of the
gathered result against the golden VectorUnit.vrgather (vd[i] = vs[idx[i]] with
out-of-range indices and tail lanes reading 0).
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


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def unpack(v):
    return [(int(v) >> (i * ELEN)) & MASKW for i in range(VLMAX)]


def golden(vs, idx, vl):
    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vreg[2] = np.array(idx, dtype=np.uint32)
    vu.vl = vl
    return [int(x) for x in vu.vrgather(1, 2)]


async def check(dut, vs, idx, vl):
    dut.vs.value = pack(vs)
    dut.idx.value = pack(idx)
    dut.vl.value = vl
    await Timer(1, units="ns")
    got = unpack(dut.vd.value)
    exp = golden(vs, idx, vl)
    for i in range(VLMAX):
        assert got[i] == exp[i], (
            f"lane{i} vl={vl} idx={idx}: got {got[i]:08x} != golden {exp[i]:08x}")


@cocotb.test()
async def test_directed(dut):
    """Corners: identity, reverse, broadcast lane0, out-of-range indices, vl gating."""
    vs = [0xA0, 0xB1, 0xC2, 0xD3, 0xE4, 0xF5, 0x16, 0x27]
    await check(dut, vs, [0, 1, 2, 3, 4, 5, 6, 7], 8)          # identity
    await check(dut, vs, [7, 6, 5, 4, 3, 2, 1, 0], 8)          # reverse
    await check(dut, vs, [0, 0, 0, 0, 0, 0, 0, 0], 8)          # broadcast lane0
    await check(dut, vs, [8, 9, 100, 0xFFFF, 3, 3, 3, 3], 8)   # OOB -> 0 for big idx
    await check(dut, vs, [0, 1, 2, 3, 4, 5, 6, 7], 4)          # vl=4: idx>=4 -> 0, tail 0
    dut._log.info("atum_vrgather: directed gather corners match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x6A77E2)
    for _ in range(8000):
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        # bias indices toward the valid range but include OOB
        idx = [rng.choice([rng.randint(0, VLMAX - 1), rng.getrandbits(32)])
               for _ in range(VLMAX)]
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, idx, vl)
    dut._log.info("atum_vrgather: 8000 random gathers match golden")
