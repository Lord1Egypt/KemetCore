"""cocotb testbench for atum_vsetvl — VL = min(AVL, VLMAX), vs the golden."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

VLMAX = 8


async def check(dut, avl):
    dut.avl.value = avl
    await Timer(1, units="ns")
    vu = g.VectorUnit()
    exp = vu.vsetvl(avl)
    assert int(dut.vl.value) == exp, f"avl={avl}: got {int(dut.vl.value)} != {exp}"


@cocotb.test()
async def test_vsetvl(dut):
    for avl in list(range(0, 20)) + [100, 255, 1 << 20, 0xFFFFFFFF]:
        await check(dut, avl)
    rng = random.Random(0x5E7)
    for _ in range(2000):
        await check(dut, rng.getrandbits(32))
    dut._log.info("atum_vsetvl: VL = min(avl, VLMAX) matches golden on edges + 2000 random")
