"""cocotb testbench for BastCore bast_mac — bit-exact vs golden.matmul dot products.

Streams length-K bf16 vector pairs through the MAC (clear on the first element,
en throughout) and checks the registered fp32 accumulator against the golden
matmul of a (1,K) x (K,1) product (bf16 inputs, fp32 accumulate).
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import bast_matmul as golden  # noqa: E402


def bf16_bits_to_f32(bits):
    """bf16 bit pattern -> python float (exact, via fp32)."""
    return float(np.uint32(bits << 16).view(np.float32))


def f32_to_bits(f):
    return int(np.float32(f).view(np.uint32))


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
    """Stream a length-K dot product; return the fp32 accumulator bits."""
    K = len(avec)
    for k in range(K):
        dut.a.value = avec[k]
        dut.b.value = bvec[k]
        dut.en.value = 1
        dut.clear.value = 1 if k == 0 else 0
        await RisingEdge(dut.clk)
    dut.en.value = 0
    dut.clear.value = 0
    await RisingEdge(dut.clk)        # let the last accumulate register settle
    return int(dut.acc.value)


@cocotb.test()
async def test_dot_products(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xBA57)

    ntested = 0
    for trial in range(400):
        K = rng.randint(1, 24)
        # bf16 patterns biased toward "tame" exponents so sums stay finite/interesting,
        # with an occasional wild value to exercise rounding/cancellation.
        def rand_bf16():
            if rng.random() < 0.15:
                return rng.getrandbits(16)
            sign = rng.getrandbits(1) << 15
            exp = rng.randint(110, 140)          # ~2^-17 .. 2^13
            man = rng.getrandbits(7)
            return sign | (exp << 7) | man
        avec = [rand_bf16() for _ in range(K)]
        bvec = [rand_bf16() for _ in range(K)]

        got = await dot(dut, avec, bvec)

        A = np.array([[bf16_bits_to_f32(x) for x in avec]], dtype=np.float32)
        B = np.array([[bf16_bits_to_f32(x)] for x in bvec], dtype=np.float32)
        with np.errstate(invalid="ignore", over="ignore"):
            exp = f32_to_bits(golden.matmul(A, B)[0, 0])

        if is_nan32(exp):
            assert is_nan32(got), f"trial {trial} K={K}: got {got:08x}, expected NaN"
        else:
            assert got == exp, (
                f"trial {trial} K={K}: got {got:08x} != exp {exp:08x}\n"
                f"a={[hex(x) for x in avec]}\nb={[hex(x) for x in bvec]}")
        ntested += 1
    dut._log.info(f"bast_mac: {ntested} fp32-accumulated bf16 dot products verified bit-exact")
