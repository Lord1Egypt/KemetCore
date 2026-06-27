"""cocotb testbench for NeithCore neith_butterfly — bit-exact vs the golden CT butterfly.

Reproduces the radix-2 Cooley-Tukey butterfly used by golden.ntt_cyclic:
    t  = v*w mod Q ; lo = (u+t) mod Q ; hi = (u-t) mod Q     (Q = 7681)
Verified over directed corners and a heavy random sweep.
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as golden  # noqa: E402

Q = golden.Q  # 7681


async def check(dut, u, v, w):
    dut.u.value = u
    dut.v.value = v
    dut.w.value = w
    await Timer(1, units="ns")
    t = (v * w) % Q
    exp_lo = (u + t) % Q
    exp_hi = (u - t) % Q
    got_lo = int(dut.lo.value)
    got_hi = int(dut.hi.value)
    assert got_lo == exp_lo, f"lo({u},{v},{w}): got {got_lo} != exp {exp_lo}"
    assert got_hi == exp_hi, f"hi({u},{v},{w}): got {got_hi} != exp {exp_hi}"


@cocotb.test()
async def test_corners(dut):
    pts = [0, 1, 2, Q - 1, Q - 2, Q // 2, 7680, 100, 4096]
    n = 0
    for u in pts:
        for v in pts:
            for w in pts:
                await check(dut, u, v, w)
                n += 1
    dut._log.info(f"butterfly: {n} directed corner butterflies verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xBEEF)
    n = 30000
    for _ in range(n):
        await check(dut, rng.randrange(Q), rng.randrange(Q), rng.randrange(Q))
    dut._log.info(f"butterfly: {n} random butterflies verified bit-exact")


@cocotb.test()
async def test_real_twiddles(dut):
    """Use the actual NTT twiddle powers (OMEGA^k) the engine will drive."""
    rng = random.Random(0x5A5A)
    twiddles = [pow(golden.OMEGA, k, Q) for k in range(golden.N)]
    n = 0
    for w in twiddles:
        for _ in range(8):
            await check(dut, rng.randrange(Q), rng.randrange(Q), w)
            n += 1
    dut._log.info(f"butterfly: {n} real-twiddle butterflies verified bit-exact")
