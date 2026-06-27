"""cocotb testbench for seth_aluctl — EXHAUSTIVE bit-exact vs golden.decode_aluop.

The input space (opcode 7b x funct3 3b x funct7 7b = 2**17) is small enough to
sweep completely, so every (opcode, funct3, funct7) is checked against the golden.
"""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


@cocotb.test()
async def test_exhaustive(dut):
    n = 0
    for opcode in range(128):
        for funct3 in range(8):
            for funct7 in range(128):
                dut.opcode.value = opcode
                dut.funct3.value = funct3
                dut.funct7.value = funct7
                await Timer(1, units="ns")
                got = int(dut.alu_op.value)
                exp = g.decode_aluop(opcode, funct3, funct7)
                assert got == exp, (
                    f"op={opcode:#04x} f3={funct3} f7={funct7:#04x}: "
                    f"got {got} exp {exp}")
                n += 1
    dut._log.info(f"seth_aluctl: {n} (opcode,funct3,funct7) combinations verified exhaustively")
