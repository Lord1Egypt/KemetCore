"""cocotb testbench for BastCore bast_fp16_mac — fp16 multiply / fp32 accumulate,
bit-exact vs golden bast_matmul.fp16_dot on streamed length-K dot products."""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import bast_matmul as golden  # noqa: E402


def fp16_bits_to_val(bits):
    """fp16 bit pattern -> numpy float16 value."""
    return np.frombuffer(int(bits & 0xFFFF).to_bytes(2, "little"), np.float16)[0]


def f32_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def reset(dut):
    dut.en.value = 0; dut.clear.value = 0; dut.a.value = 0; dut.b.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def dot(dut, avec, bvec):
    for k in range(len(avec)):
        dut.a.value = int(avec[k]); dut.b.value = int(bvec[k])
        dut.en.value = 1; dut.clear.value = 1 if k == 0 else 0
        await RisingEdge(dut.clk)
    dut.en.value = 0; dut.clear.value = 0
    await RisingEdge(dut.clk)
    return int(dut.acc.value)


@cocotb.test()
async def test_fp16_dot_products(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xBA5F16)

    for trial in range(400):
        K = rng.randint(1, 24)

        def rand_fp16():
            if rng.random() < 0.15:
                return rng.getrandbits(16)              # wild (incl subnormal/inf/nan)
            sign = rng.getrandbits(1) << 15
            exp = rng.randint(8, 22)                    # tame exponents (~2^-7..2^7)
            man = rng.getrandbits(10)
            return sign | (exp << 10) | man

        abits = [rand_fp16() for _ in range(K)]
        bbits = [rand_fp16() for _ in range(K)]
        got = await dot(dut, abits, bbits)

        avals = [fp16_bits_to_val(x) for x in abits]
        bvals = [fp16_bits_to_val(x) for x in bbits]
        with np.errstate(invalid="ignore", over="ignore"):
            exp = f32_to_bits(golden.fp16_dot(avals, bvals))

        if is_nan32(exp):
            assert is_nan32(got), f"trial {trial} K={K}: got {got:08x}, expected NaN"
        else:
            assert got == exp, f"trial {trial} K={K}: got {got:08x} exp {exp:08x}"

    dut._log.info("bast_fp16_mac verified bit-exact vs golden fp16_dot (400 dot products)")
