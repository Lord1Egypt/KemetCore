"""cocotb testbench for SethCore seth_csru — bit-exact vs golden csr_bank_step."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as golden  # noqa: E402

F3 = [0b001, 0b010, 0b011, 0b101, 0b110, 0b111]


async def reset(dut):
    dut.valid.value = 0
    dut.funct3.value = 0
    dut.csr_addr.value = 0
    dut.rs1.value = 0
    dut.zimm.value = 0
    dut.rd_addr.value = 0
    dut.rst.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_csru(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xC5A)
    bank = [0] * 16

    for _ in range(4000):
        f3 = rng.choice(F3)
        addr = rng.randint(0, 4095)
        rs1 = rng.getrandbits(32)
        zimm = rng.getrandbits(5)
        # present inputs; rd_val is combinational over the CURRENT bank
        dut.valid.value = 1
        dut.funct3.value = f3
        dut.csr_addr.value = addr
        dut.rs1.value = rs1
        dut.zimm.value = zimm
        await Timer(1, units="ns")
        exp_rd = golden.csr_bank_step(bank, f3, addr, rs1, zimm)
        assert int(dut.rd_val.value) == exp_rd, \
            f"rd_val addr={addr:#x} f3={f3}: {int(dut.rd_val.value):08x}!={exp_rd:08x}"
        await RisingEdge(dut.clk)        # commit the write

    # verify the whole bank matches
    dut.valid.value = 0
    for a in range(16):
        dut.rd_addr.value = a
        await Timer(1, units="ns")
        assert int(dut.rd_data.value) == bank[a], \
            f"bank[{a}]: {int(dut.rd_data.value):08x}!={bank[a]:08x}"
    dut._log.info("seth_csru verified bit-exact vs golden csr_bank_step (bank + rd_val)")
