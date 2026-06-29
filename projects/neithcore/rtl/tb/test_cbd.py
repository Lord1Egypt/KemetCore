"""cocotb testbench for NeithCore neith_cbd — bit-exact vs golden._cbd_coeff.

Each beat presents 2*ETA random bits (a in [ETA-1:0], b in [2*ETA-1:ETA]); the engine
computes (popcount(a) - popcount(b)) mod Q. We exhaustively cover all 2^(2*ETA) bit
patterns and random streams, comparing against golden._cbd_coeff.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as golden  # noqa: E402

Q = golden.Q
N = golden.N      # 256
ETA = golden.ETA  # 2


def bits_of(x, n):
    return [(x >> i) & 1 for i in range(n)]


async def reset(dut):
    dut.start.value = 0
    dut.in_valid.value = 0
    dut.in_data.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run(dut, words):
    dut.start.value = 1
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for j in range(N):
        dut.in_valid.value = 1
        dut.in_data.value = int(words[j]) & 0x1FFF
        await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    for _ in range(50):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "engine did not assert done in time"
    out = []
    for addr in range(N):
        dut.rd_addr.value = addr
        await Timer(1, units="ns")
        out.append(int(dut.out_data.value))
    return out


def expected(word):
    a_bits = bits_of(word & ((1 << ETA) - 1), ETA)
    b_bits = bits_of((word >> ETA) & ((1 << ETA) - 1), ETA)
    return golden._cbd_coeff(a_bits, b_bits)


@cocotb.test()
async def test_cbd(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xCB000)

    # exhaustive: all 2^(2*ETA) bit patterns, tiled across the 256 lanes
    npat = 1 << (2 * ETA)
    words = [i % npat for i in range(N)]
    got = await run(dut, words)
    assert got == [expected(w) for w in words], "exhaustive CBD pattern mismatch"

    # random streams
    for _ in range(8):
        words = [rng.getrandbits(2 * ETA) for _ in range(N)]
        got = await run(dut, words)
        assert got == [expected(w) for w in words]

    dut._log.info("neith_cbd: exhaustive 2*ETA-bit patterns + random match golden._cbd_coeff")
