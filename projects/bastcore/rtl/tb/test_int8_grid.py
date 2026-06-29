"""cocotb testbench for BastCore bast_int8_grid — bit-exact vs golden.int8_matmul."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import bast_matmul as golden  # noqa: E402

R = 4
C = 4


async def run_matmul(dut, Ab, Bb, K):
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
    for t in range(R + C + K + 2):
        aval = 0
        for i in range(R):
            k = t - i
            if 0 <= k < K:
                aval |= (int(Ab[i][k]) & 0xFF) << (8 * i)
        bval = 0
        for j in range(C):
            k = t - j
            if 0 <= k < K:
                bval |= (int(Bb[k][j]) & 0xFF) << (8 * j)
        dut.a_in.value = aval
        dut.b_in.value = bval
        await RisingEdge(dut.clk)
    dut.en.value = 0
    out = [[0] * C for _ in range(R)]
    for i in range(R):
        for j in range(C):
            dut.rd_row.value = i
            dut.rd_col.value = j
            await Timer(1, units="ns")
            out[i][j] = int(dut.out_acc.value) & 0xFFFFFFFF
    return out


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


async def check(dut, Ab, Bb, K, tag):
    got = await run_matmul(dut, Ab, Bb, K)
    exp = golden.int8_matmul(Ab, Bb, K, R, C)
    for i in range(R):
        for j in range(C):
            assert got[i][j] == exp[i][j], \
                f"{tag} K={K} ({i},{j}): {got[i][j]:08x}!={exp[i][j]:08x}"


@cocotb.test()
async def test_int8_grid(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x1287)

    # directed: max-magnitude and sign extremes
    Ab = [[127] * 8 for _ in range(R)]
    Bb = [[127] * C for _ in range(8)]
    await check(dut, Ab, Bb, 8, "maxpos")
    Ab = [[0x80] * 8 for _ in range(R)]      # -128
    await check(dut, Ab, Bb, 8, "negpos")

    for trial in range(120):
        K = rng.randint(1, 24)
        Ab = [[rng.randint(0, 255) for _ in range(K)] for _ in range(R)]
        Bb = [[rng.randint(0, 255) for _ in range(C)] for _ in range(K)]
        await check(dut, Ab, Bb, K, f"rand{trial}")
    dut._log.info("bast_int8_grid verified bit-exact vs golden.int8_matmul")
