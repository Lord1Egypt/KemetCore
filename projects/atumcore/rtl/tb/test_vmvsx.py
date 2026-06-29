"""cocotb testbench for atum_vmvsx — AtumCore scalar<->vector element-0 moves.

Checks both halves against the golden VectorUnit: scalar_out == vmv.x.s (element 0 of
the source, any vl) and vec_out == vmv.s.x (vd_old with element 0 <- scalar_in when
vl>0, else unchanged; elements 1.. always the undisturbed tail).
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


async def check(dut, vs, scalar_in, vd_old, vl):
    dut.vs.value = pack(vs)
    dut.scalar_in.value = scalar_in & MASKW
    dut.vd_old.value = pack(vd_old)
    dut.vl.value = vl
    await Timer(1, units="ns")

    vu = g.VectorUnit()
    vu.vreg[1] = np.array(vs, dtype=np.uint32)
    vu.vreg[3] = np.array(vd_old, dtype=np.uint32)
    vu.vl = vl
    exp_scalar = vu.vmv_x_s(1)
    vu.vmv_s_x(3, scalar_in)
    exp_vec = [int(x) for x in vu.vreg[3].astype(np.uint32)]

    got_scalar = int(dut.scalar_out.value)
    got_vec = unpack(dut.vec_out.value)
    assert got_scalar == exp_scalar, (
        f"vmv.x.s vl={vl}: got {got_scalar:08x} != golden {exp_scalar:08x}")
    assert got_vec == exp_vec, (
        f"vmv.s.x vl={vl} scalar={scalar_in:08x}: got "
        f"{[f'{x:08x}' for x in got_vec]} != golden {[f'{x:08x}' for x in exp_vec]}")


@cocotb.test()
async def test_directed(dut):
    vs = [0xDEADBEEF, 0x11111111, 0x22222222, 0x33333333,
          0x44444444, 0x55555555, 0x66666666, 0x77777777]
    old = [0xA0A0A0A0] * VLMAX
    for vl in range(VLMAX + 1):
        await check(dut, vs, 0xCAFEBABE, old, vl)
    await check(dut, vs, 0x00000000, old, 8)
    await check(dut, vs, 0xFFFFFFFF, old, 1)
    dut._log.info("atum_vmvsx: directed extract/insert across all vl match golden")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x5CA1A4)
    for _ in range(4000):
        vs = [rng.getrandbits(32) for _ in range(VLMAX)]
        old = [rng.getrandbits(32) for _ in range(VLMAX)]
        scalar_in = rng.getrandbits(32)
        vl = rng.randint(0, VLMAX)
        await check(dut, vs, scalar_in, old, vl)
    dut._log.info("atum_vmvsx: 4000 random scalar<->vector elem-0 moves match golden")
