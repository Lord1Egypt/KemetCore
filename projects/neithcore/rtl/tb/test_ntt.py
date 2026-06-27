"""cocotb testbench for NeithCore neith_ntt — bit-exact vs golden.ntt_cyclic.

Streams 256 coefficients into the engine, runs the multicycle forward NTT, reads
the 256 results back by address, and checks them against
golden.ntt_cyclic(vec, OMEGA) (q = 7681). Covers impulses, constants, ramps and
random vectors, including a back-to-back second transform.
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
N = golden.N  # 256


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


async def run_ntt(dut, vec):
    # start pulse (engine -> LOAD)
    dut.start.value = 1
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    # stream 256 coefficients
    for j in range(N):
        dut.in_valid.value = 1
        dut.in_data.value = vec[j]
        await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    # wait for completion
    for _ in range(2000):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "engine did not assert done in time"
    # read results back by address (combinational)
    out = []
    for addr in range(N):
        dut.rd_addr.value = addr
        await Timer(1, units="ns")
        out.append(int(dut.out_data.value))
    return out


async def check(dut, vec):
    got = await run_ntt(dut, vec)
    exp = golden.ntt_cyclic(vec, golden.OMEGA)
    assert got == exp, (
        f"NTT mismatch (first differing index): "
        f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")


@cocotb.test()
async def test_directed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    # impulse -> NTT is all-ones * a[0]
    await check(dut, [5] + [0] * (N - 1))
    # constant
    await check(dut, [3] * N)
    # ramp mod Q
    await check(dut, [(i * 37) % Q for i in range(N)])
    # all max
    await check(dut, [Q - 1] * N)
    dut._log.info("neith_ntt: directed vectors (impulse/const/ramp/max) verified bit-exact")


@cocotb.test()
async def test_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x117700)
    ntrans = 24
    for t in range(ntrans):
        vec = [rng.randrange(Q) for _ in range(N)]
        await check(dut, vec)
    dut._log.info(f"neith_ntt: {ntrans} random 256-point transforms verified bit-exact")
