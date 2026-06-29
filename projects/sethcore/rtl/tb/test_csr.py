"""cocotb testbench for SethCore seth_csr — bit-exact vs golden csr_op.

Sweeps the six Zicsr funct3 encodings against random CSR/rs1/uimm values and
checks the rd value, next CSR value, and write enable.
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as golden  # noqa: E402

F3 = [0b001, 0b010, 0b011, 0b101, 0b110, 0b111]


async def check(dut, f3, csr_in, rs1, zimm):
    dut.funct3.value = f3
    dut.csr_in.value = csr_in
    dut.rs1.value = rs1
    dut.zimm.value = zimm
    await Timer(1, units="ns")
    rd_val, csr_out, we = golden.csr_op(f3, csr_in, rs1, zimm)
    assert int(dut.rd_val.value) == rd_val, f"rd f3={f3} csr={csr_in:08x}: {int(dut.rd_val.value):08x}!={rd_val:08x}"
    assert int(dut.csr_out.value) == csr_out, f"csr_out f3={f3} csr={csr_in:08x} op rs1={rs1:08x} z={zimm}: {int(dut.csr_out.value):08x}!={csr_out:08x}"
    assert int(dut.csr_we.value) == we, f"we f3={f3} rs1={rs1:08x} z={zimm}: {int(dut.csr_we.value)}!={we}"


@cocotb.test()
async def test_csr(dut):
    # directed corners
    corners = [0, 1, 0xFFFFFFFF, 0x80000000, 0x0000FFFF, 0xDEADBEEF]
    for f3 in F3:
        for csr_in in corners:
            for op in corners:
                await check(dut, f3, csr_in, op, op & 0x1F)
    # zero-operand (no-write) cases for RS/RC and their imm variants
    for f3 in [0b010, 0b011, 0b110, 0b111]:
        await check(dut, f3, 0xCAFEBABE, 0, 0)
    # random sweep
    for _ in range(8000):
        f3 = random.choice(F3)
        await check(dut, f3, random.getrandbits(32), random.getrandbits(32),
                    random.getrandbits(5))
    dut._log.info("seth_csr verified bit-exact vs golden csr_op")
