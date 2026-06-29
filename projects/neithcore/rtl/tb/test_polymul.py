"""cocotb testbench for NeithCore neith_polymul — full negacyclic poly multiply.

Loads two length-256 polynomials a, b, runs the integrated ntt -> pointwise -> intt
pipeline, reads the product, and checks it against golden.poly_mul_ntt (and the
independent golden.poly_mul_schoolbook). Covers impulse/constant corners and random
polynomials, plus a back-to-back second multiply.
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


async def run(dut, a, b):
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
    # ntt(a) + ntt(b) + pointwise + intt: a few thousand cycles, poll done
    for _ in range(20000):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "polymul did not assert done in time"
    out = []
    for addr in range(N):
        dut.rd_addr.value = addr
        await Timer(1, units="ns")
        out.append(int(dut.out_data.value))
    return out


@cocotb.test()
async def test_polymul(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xDEC0DE)

    # impulse: a = 1 (constant term) -> a*b == b
    a = [0] * N
    a[0] = 1
    b = [(i * 3 + 1) % Q for i in range(N)]
    got = await run(dut, a, b)
    assert got == golden.poly_mul_ntt(a, b) == b

    # x * b is a negacyclic shift (checks the psi twist end to end)
    a = [0] * N
    a[1] = 1
    got = await run(dut, a, b)
    assert got == golden.poly_mul_ntt(a, b)

    # random polynomials, bit-exact vs both golden multipliers, back-to-back
    for _ in range(6):
        a = [rng.randrange(Q) for _ in range(N)]
        b = [rng.randrange(Q) for _ in range(N)]
        got = await run(dut, a, b)
        assert got == golden.poly_mul_ntt(a, b)
        assert got == golden.poly_mul_schoolbook(a, b)

    dut._log.info("neith_polymul: impulse/shift/random negacyclic products match golden")
