"""cocotb testbench for NeithCore neith_polyaddsub — bit-exact vs golden padd/psub.

Streams 256 (A[i], B[i]) coefficient pairs with op latched at start (0 padd / 1 psub),
reads the 256 results back by address, and checks them against golden.padd / golden.psub
(both mod Q). Covers zero/Q-1/wrap corners, both ops back-to-back, and random vectors.
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
    dut.op.value = 0
    dut.in_valid.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run(dut, a, b, op):
    dut.start.value = 1
    dut.op.value = op
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
async def test_polyaddsub(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xADD5)

    a0 = [0, Q - 1, 1, Q - 1, 100, 0, Q // 2, Q - 1] + [(i * 11) % Q for i in range(N - 8)]
    b0 = [0, 1, Q - 1, Q - 1, 200, Q - 1, Q // 2, 0] + [(i * 7 + 3) % Q for i in range(N - 8)]
    for op, ref in ((0, golden.padd), (1, golden.psub)):
        got = await run(dut, a0, b0, op)
        exp = ref(a0, b0)
        assert got == exp, ("padd" if op == 0 else "psub") + " corner mismatch at " + \
            str(next((i for i in range(N) if got[i] != exp[i]), -1))

    for _ in range(8):
        a = [rng.randrange(Q) for _ in range(N)]
        b = [rng.randrange(Q) for _ in range(N)]
        op = rng.randint(0, 1)
        got = await run(dut, a, b, op)
        exp = (golden.psub if op else golden.padd)(a, b)
        assert got == exp

    dut._log.info("neith_polyaddsub: padd/psub corners + random match golden")
