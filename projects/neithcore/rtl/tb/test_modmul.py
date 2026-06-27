"""cocotb testbench for NeithCore neith_modmul — bit-exact vs (a*b) % Q.

Q = 7681 (the golden's NTT-friendly modulus). Checks the Barrett-reduction
multiplier over directed corners, a heavy random sweep, and the worst-case
near-modulus operands that stress the conditional-subtraction count.
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as golden  # noqa: E402

Q = golden.Q  # 7681


async def check(dut, a, b):
    dut.a.value = a
    dut.b.value = b
    await Timer(1, units="ns")
    got = int(dut.r.value)
    exp = (a * b) % Q
    assert got == exp, f"{a}*{b} mod {Q}: got {got} != exp {exp}"


@cocotb.test()
async def test_corners(dut):
    pts = [0, 1, 2, Q - 1, Q - 2, Q // 2, 7680, 7679, 100, 4096, 8000 % Q]
    n = 0
    for a in pts:
        for b in pts:
            await check(dut, a % Q, b % Q)
            n += 1
    dut._log.info(f"modmul: {n} directed corner products verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0x1EE7)
    n = 30000
    for _ in range(n):
        await check(dut, rng.randrange(Q), rng.randrange(Q))
    dut._log.info(f"modmul: {n} random products verified bit-exact")


@cocotb.test()
async def test_near_modulus(dut):
    """Operands near Q-1 maximise the Barrett remainder before reduction."""
    hi = list(range(Q - 40, Q))
    n = 0
    for a in hi:
        for b in hi:
            await check(dut, a, b)
            n += 1
    dut._log.info(f"modmul: {n} near-modulus products verified bit-exact")
