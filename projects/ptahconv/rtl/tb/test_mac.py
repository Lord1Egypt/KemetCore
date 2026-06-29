"""cocotb testbench for PtahConv ptah_mac — bit-exact vs golden dot_seq."""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ptah_conv as golden  # noqa: E402


def f2b(x):
    return int(np.frombuffer(struct.pack("<f", np.float32(x)), np.uint32)[0])


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


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
    return int(dut.acc.value)


def rand_f32(rng):
    # tame exponents keep sums finite/interesting, with occasional wild values
    if rng.random() < 0.08:
        return rng.getrandbits(32)
    sign = rng.getrandbits(1) << 31
    exp = rng.randint(118, 132)
    man = rng.getrandbits(23)
    return sign | (exp << 23) | man


@cocotb.test()
async def test_dot(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x97A4)

    # directed
    for av, bv in [([f2b(1.0)], [f2b(2.0)]),
                   ([f2b(1.0)] * 8, [f2b(1.0)] * 8),
                   ([f2b(0.1)] * 16, [f2b(0.1)] * 16),
                   ([f2b(-3.0), f2b(2.5)], [f2b(4.0), f2b(-1.0)])]:
        got = await dot(dut, av, bv)
        exp = golden.dot_seq(av, bv)
        assert got == exp, f"directed: {got:08x}!={exp:08x}"

    for _ in range(500):
        K = rng.randint(1, 24)
        av = [rand_f32(rng) for _ in range(K)]
        bv = [rand_f32(rng) for _ in range(K)]
        got = await dot(dut, av, bv)
        exp = golden.dot_seq(av, bv)
        if is_nan32(exp):
            assert is_nan32(got), f"K={K}: expected NaN got {got:08x}"
        else:
            assert got == exp, f"K={K}: {got:08x}!={exp:08x}"
    dut._log.info("ptah_mac verified bit-exact vs golden dot_seq")
