"""cocotb testbench for NeithCore neith_pointwise — bit-exact vs golden.pointwise.

Streams 256 (A[i], B[i]) coefficient pairs into the engine, runs the streamed
element-wise modular multiply, reads the 256 results back by address, and checks them
against golden.pointwise(A, B) = [A[i]*B[i] % Q]. Covers zeros/ones/Q-1 corners,
back-to-back runs, and random vectors. Also checks the pointwise stage composes into
golden.poly_mul_ntt (ntt -> pointwise -> intt) for a random pair.
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
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_pointwise(dut, a, b):
    dut.start.value = 1
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for j in range(N):
        dut.in_valid.value = 1
        dut.a_in.value = a[j] % Q
        dut.b_in.value = b[j] % Q
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


@cocotb.test()
async def test_pointwise(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xC0DE)

    cases = [
        ([0] * N, [123] * N),                                    # zero A -> all 0
        ([1] * N, [(i * 7) % Q for i in range(N)]),              # identity A
        ([Q - 1] * N, [Q - 1] * N),                              # (-1)*(-1) = 1
        ([(i * 13) % Q for i in range(N)], [(i * 5 + 1) % Q for i in range(N)]),
    ]
    for a, b in cases:
        got = await run_pointwise(dut, a, b)
        exp = golden.pointwise(a, b)
        assert got == exp, f"pointwise mismatch (first diff at "\
            f"{next((i for i in range(N) if got[i] != exp[i]), -1)})"

    # random back-to-back runs
    for _ in range(8):
        a = [rng.randrange(Q) for _ in range(N)]
        b = [rng.randrange(Q) for _ in range(N)]
        got = await run_pointwise(dut, a, b)
        assert got == golden.pointwise(a, b)

    # integration: pointwise is the middle of poly_mul_ntt (ntt -> pointwise -> intt)
    a = [rng.randrange(Q) for _ in range(N)]
    b = [rng.randrange(Q) for _ in range(N)]
    A, B = golden.ntt(a), golden.ntt(b)
    hw_C = await run_pointwise(dut, A, B)
    assert golden.intt(hw_C) == golden.poly_mul_ntt(a, b)

    dut._log.info("neith_pointwise: corners + random + poly_mul_ntt integration match golden")
