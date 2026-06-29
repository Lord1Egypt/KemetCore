"""cocotb testbench for BastCore bast_int8_mac — bit-exact vs golden int8_dot."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import bast_matmul as golden  # noqa: E402


async def reset(dut):
    dut.en.value = 0
    dut.clear.value = 0
    dut.a.value = 0
    dut.b.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def dot(dut, avec, bvec):
    for k in range(len(avec)):
        dut.a.value = avec[k]
        dut.b.value = bvec[k]
        dut.en.value = 1
        dut.clear.value = 1 if k == 0 else 0
        await RisingEdge(dut.clk)
    dut.en.value = 0
    dut.clear.value = 0
    await RisingEdge(dut.clk)
    return int(dut.acc.value) & 0xFFFFFFFF


@cocotb.test()
async def test_int8_mac(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xB18)

    # directed: max-magnitude products and sign combinations
    for av, bv in [([127], [127]), ([-128], [-128]), ([-128], [127]),
                   ([127] * 24, [127] * 24), ([-128] * 24, [127] * 24),
                   ([0], [0]), ([1, -1, 1, -1], [127, 127, 127, 127])]:
        av8 = [x & 0xFF for x in av]
        bv8 = [x & 0xFF for x in bv]
        got = await dot(dut, av8, bv8)
        assert got == golden.int8_dot(av8, bv8), f"{av},{bv}: {got:08x}"

    for _ in range(2000):
        K = rng.randint(1, 40)
        av = [rng.randint(0, 255) for _ in range(K)]
        bv = [rng.randint(0, 255) for _ in range(K)]
        got = await dot(dut, av, bv)
        assert got == golden.int8_dot(av, bv), f"K={K}: {got:08x}"
    dut._log.info("bast_int8_mac verified bit-exact vs golden int8_dot")
