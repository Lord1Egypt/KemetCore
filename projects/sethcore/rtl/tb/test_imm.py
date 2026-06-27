"""cocotb testbench for seth_imm — bit-exact vs golden.decode_imm.

Drives 32-bit instruction words and checks the generated immediate against the
golden RV32 immediate decoder, over directed per-format vectors and random words
(every opcode class, including R-type/system -> 0).
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


async def check(dut, ins):
    dut.ins.value = ins
    await Timer(1, units="ns")
    got = int(dut.imm.value)
    exp = g.decode_imm(ins)
    assert got == exp, f"ins={ins:08x} (op={ins & 0x7F:#04x}): got {got:08x} exp {exp:08x}"


@cocotb.test()
async def test_directed(dut):
    """Each format with corner immediates, built by the golden field encoders."""
    n = 0
    for imm in (0, 1, -1, 2047, -2048, 1365, -1366, 0x555, -0x556):
        for ins in (g._I(imm, 1, 0x0, 5, 0x13), g._I(imm, 2, 0x2, 6, 0x03),
                    g._I(imm, 2, 0x0, 1, 0x67), g._S(imm, 7, 2, 0x2, 0x23)):
            await check(dut, ins); n += 1
    for imm in (0, 2, -2, 4094, -4096, 1024, -2048, 256):
        await check(dut, g._B(imm, 2, 1, 0x0, 0x63)); n += 1
    for imm in (0x00000000, 0x12345000, 0xABCDE000, 0xFFFFF000, 0x80000000):
        await check(dut, g._U(imm, 5, 0x37)); n += 1
        await check(dut, g._U(imm, 5, 0x17)); n += 1
    for imm in (0, 2, -2, 0xFFFFE, -0x100000, 2048, -2048):
        await check(dut, g._J(imm, 1, 0x6F)); n += 1
    await check(dut, g._R(0, 3, 2, 0x0, 1, 0x33))            # R-type -> 0
    await check(dut, g.assemble([("ecall",)])[0])            # system -> 0
    n += 2
    dut._log.info(f"seth_imm: {n} directed per-format immediates verified bit-exact")


@cocotb.test()
async def test_random(dut):
    """Random 32-bit words — covers every opcode (valid formats and unknown -> 0)."""
    rng = random.Random(0x1117)
    n = 40000
    for _ in range(n):
        await check(dut, rng.getrandbits(32))
    dut._log.info(f"seth_imm: {n} random instruction words verified bit-exact")


@cocotb.test()
async def test_random_valid_ops(dut):
    """Bias the opcode to the immediate-bearing formats so each is hammered."""
    rng = random.Random(0xABCD)
    ops = [0x13, 0x03, 0x67, 0x23, 0x63, 0x37, 0x17, 0x6F, 0x33, 0x73]
    n = 0
    for _ in range(30000):
        ins = (rng.getrandbits(32) & ~0x7F) | rng.choice(ops)
        await check(dut, ins); n += 1
    dut._log.info(f"seth_imm: {n} opcode-biased instruction words verified bit-exact")
