"""cocotb testbench for GebCore geb_spmac — bit-exact vs golden.sparse_matmul.

For each output element it streams the K/2 kept (value, index) pairs of a
compressed column together with that group's 4 fp32 activations, and checks the
registered fp32 accumulator against golden.sparse_matmul (fp32 mul + fp32
accumulate over only the kept 2:4 lanes). Random matrices are pruned/compressed
by the golden, so the hardware sees exactly the metadata the model produced.
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import geb_sparse as golden  # noqa: E402


def f32_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def reset(dut):
    dut.en.value = 0
    dut.clear.value = 0
    dut.a_group.value = 0
    dut.idx.value = 0
    dut.val.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def spdot(dut, a_row, values_col, indices_col):
    """Stream one sparse output element; return the fp32 accumulator bits."""
    KH = len(values_col)
    for s in range(KH):
        grp = (s // 2) * 4
        a_group = 0
        for lane in range(4):
            a_group |= (f32_to_bits(a_row[grp + lane]) & 0xFFFFFFFF) << (32 * lane)
        dut.a_group.value = a_group
        dut.idx.value = int(indices_col[s])
        dut.val.value = f32_to_bits(values_col[s])
        dut.en.value = 1
        dut.clear.value = 1 if s == 0 else 0
        await RisingEdge(dut.clk)
    dut.en.value = 0
    dut.clear.value = 0
    await RisingEdge(dut.clk)        # let the last accumulate register settle
    return int(dut.acc.value)


@cocotb.test()
async def test_sparse_matmul(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = np.random.default_rng(0x6EB5)
    pyrng = random.Random(0x6EB5)

    ntested = 0
    for trial in range(80):
        K = pyrng.choice([4, 8, 12, 16, 20])
        M = pyrng.randint(1, 3)
        N = pyrng.randint(1, 4)
        A = rng.standard_normal((M, K)).astype(np.float32) * np.float32(2.0)
        W = rng.standard_normal((K, N)).astype(np.float32) * np.float32(2.0)

        Wp = golden.prune_2of4(W)
        values, indices = golden.compress_2of4(Wp)
        # The hardware mirrors sparse_matmul exactly (kept lanes in metadata order,
        # fp32 mul + fp32 accumulate). NB: golden.dense_matmul(A, Wp) is only ~equal,
        # not bit-identical, because fp32 summation is non-associative and uses a
        # different lane order — so the bit-exact target is sparse_matmul.
        ref = golden.sparse_matmul(A, values, indices)

        for i in range(M):
            for j in range(N):
                got = await spdot(dut, A[i], values[:, j], indices[:, j])
                exp = f32_to_bits(ref[i, j])
                if is_nan32(exp):
                    assert is_nan32(got), f"trial {trial} ({i},{j}): got {got:08x}, want NaN"
                else:
                    assert got == exp, (
                        f"trial {trial} K={K} cell ({i},{j}): got {got:08x} != exp {exp:08x}")
                ntested += 1
    dut._log.info(f"geb_spmac: {ntested} 2:4 sparse output elements verified bit-exact")
