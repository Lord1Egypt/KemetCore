"""cocotb testbench for SethCore seth_branch — bit-exact vs golden branch_taken."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as golden  # noqa: E402

F3 = [0b000, 0b001, 0b100, 0b101, 0b110, 0b111]


async def check(dut, f3, a, b):
    dut.funct3.value = f3
    dut.rs1.value = a
    dut.rs2.value = b
    await Timer(1, units="ns")
    exp = 1 if golden.branch_taken(f3, a, b) else 0
    assert int(dut.taken.value) == exp, \
        f"f3={f3:#05b} a={a:08x} b={b:08x}: {int(dut.taken.value)}!={exp}"


@cocotb.test()
async def test_branch(dut):
    corners = [0, 1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0xFFFFFFFE]
    for f3 in F3:
        for a in corners:
            for b in corners:
                await check(dut, f3, a, b)
    # invalid encodings read as not-taken
    for f3 in [0b010, 0b011]:
        await check(dut, f3, 5, 5)
    for _ in range(8000):
        await check(dut, random.choice(F3), random.getrandbits(32), random.getrandbits(32))
    dut._log.info("seth_branch verified bit-exact vs golden branch_taken")
