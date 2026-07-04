"""cocotb testbench for BastCore bast_mac_grid — bit-exact vs golden.fp16_dot per cell.

Drives the default 4x4 output-stationary systolic array. For an (R,K)x(K,C) matmul
each PE(i,j) must accumulate sum_k A[i][k]*B[k][j] in the golden's k-order, so the
A-stream of row i is injected skewed by i cycles and the B-stream of column j skewed
by j cycles, zero-padded outside the K-long window (a true fp32 no-op). After the
array drains, every accumulator acc[i][j] is read back and checked against
per-cell golden.fp16_dot (fp16 inputs, fp16 product, fp32 accumulate).
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import bast_matmul as golden  # noqa: E402

R = 4   # must match bast_mac_grid default parameters
C = 4


def fp16_bits_to_val(bits):
    return np.frombuffer(int(bits & 0xFFFF).to_bytes(2, "little"), np.float16)[0]


def f32_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def reset(dut):
    dut.en.value = 0
    dut.clear.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.rd_row.value = 0
    dut.rd_col.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_matmul(dut, Ab, Bb, K):
    """Ab: R x K bf16 patterns, Bb: K x C bf16 patterns. Returns R x C fp32 bits."""
    # flush every accumulator + propagation register before the matmul
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.clear.value = 0
    dut.en.value = 0
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut.en.value = 1
    # stream skewed, zero-padded operands until the array fully drains
    for t in range(R + C + K + 2):
        aval = 0
        for i in range(R):
            k = t - i
            if 0 <= k < K:
                aval |= int(Ab[i][k]) << (16 * i)
        bval = 0
        for j in range(C):
            k = t - j
            if 0 <= k < K:
                bval |= int(Bb[k][j]) << (16 * j)
        dut.a_in.value = aval
        dut.b_in.value = bval
        await RisingEdge(dut.clk)
    dut.en.value = 0
    # read every accumulator combinationally
    out = [[0] * C for _ in range(R)]
    for i in range(R):
        for j in range(C):
            dut.rd_row.value = i
            dut.rd_col.value = j
            await Timer(1, units="ns")
            out[i][j] = int(dut.out_acc.value)
    return out


def rand_fp16(rng):
    if rng.random() < 0.10:
        return rng.getrandbits(16)
    sign = rng.getrandbits(1) << 15
    exp = rng.randint(10, 20)            # tame fp16 magnitudes so 4x4 sums stay finite
    man = rng.getrandbits(10)
    return sign | (exp << 10) | man


async def check(dut, Ab, Bb, K, tag):
    got = await run_matmul(dut, Ab, Bb, K)
    Av = [[fp16_bits_to_val(Ab[i][k]) for k in range(K)] for i in range(R)]
    Bv = [[fp16_bits_to_val(Bb[k][j]) for j in range(C)] for k in range(K)]
    for i in range(R):
        for j in range(C):
            with np.errstate(invalid="ignore", over="ignore"):
                e = f32_to_bits(golden.fp16_dot(Av[i], [Bv[k][j] for k in range(K)]))
            g = got[i][j]
            if is_nan32(e):
                assert is_nan32(g), f"{tag} K={K} ({i},{j}): got {g:08x}, expected NaN"
            else:
                assert g == e, f"{tag} K={K} cell ({i},{j}): got {g:08x} != exp {e:08x}"


@cocotb.test()
async def test_directed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    one = 0x3C00   # fp16 1.0
    two = 0x4000   # fp16 2.0
    # identity-ish: A all ones, B all ones, K=4 -> every cell == 4.0
    Ab = [[one] * 4 for _ in range(R)]
    Bb = [[one] * C for _ in range(4)]
    await check(dut, Ab, Bb, 4, "ones")
    # zeros -> all zero
    await check(dut, [[0] * 3 for _ in range(R)], [[0] * C for _ in range(3)], 3, "zeros")
    # distinct constants, K=1: cell(i,j) = a_i * b_j
    Ab = [[two] for _ in range(R)]
    Bb = [[two] * C]
    await check(dut, Ab, Bb, 1, "k1")
    dut._log.info("bast_fp16_grid: directed matmuls verified bit-exact")


@cocotb.test()
async def test_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x6217D)
    for trial in range(60):
        K = rng.choice([1, 2, 3, 4, 8, 16, 24])
        Ab = [[rand_fp16(rng) for _ in range(K)] for _ in range(R)]
        Bb = [[rand_fp16(rng) for _ in range(C)] for _ in range(K)]
        await check(dut, Ab, Bb, K, f"rand{trial}")
    dut._log.info("bast_fp16_grid: 60 random 4x4 fp16 matmuls verified bit-exact vs golden")
