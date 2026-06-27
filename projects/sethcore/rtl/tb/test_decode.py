"""cocotb testbench for seth_decode — bit-exact vs golden.decode_ctrl.

Checks the full control word (10 signals) against the golden over an exhaustive
opcode x funct7 sweep (the only fields decode depends on) and a large random
instruction stream.
"""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


def ctrl_of(dut):
    return {
        "reg_write": int(dut.reg_write.value),
        "alu_src_imm": int(dut.alu_src_imm.value),
        "a_src_pc": int(dut.a_src_pc.value),
        "mem_read": int(dut.mem_read.value),
        "mem_write": int(dut.mem_write.value),
        "branch": int(dut.branch.value),
        "jump": int(dut.jump.value),
        "jalr": int(dut.jalr.value),
        "is_mdu": int(dut.is_mdu.value),
        "wb_sel": int(dut.wb_sel.value),
    }


async def check(dut, ins):
    dut.ins.value = ins
    await Timer(1, units="ns")
    assert ctrl_of(dut) == g.decode_ctrl(ins), f"ins={ins:08x} (op={ins & 0x7F:#04x})"


@cocotb.test()
async def test_opcode_funct7_sweep(dut):
    """Every opcode x funct7 (the fields decode reads), other bits randomised."""
    rng = random.Random(0xDEC0DE)
    n = 0
    for op in range(128):
        for f7 in range(128):
            mid = rng.getrandbits(18)        # ins[24:7]
            ins = (f7 << 25) | (mid << 7) | op
            await check(dut, ins)
            n += 1
    dut._log.info(f"seth_decode: {n} opcode x funct7 control words verified bit-exact")


@cocotb.test()
async def test_random(dut):
    rng = random.Random(0xC0FFEE)
    n = 50000
    for _ in range(n):
        await check(dut, rng.getrandbits(32))
    dut._log.info(f"seth_decode: {n} random instruction words verified bit-exact")
