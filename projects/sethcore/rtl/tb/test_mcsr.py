"""cocotb testbench for SethCore seth_mcsr — RV32 M-mode CSR file, bit-exact vs
golden seth_mcsr_model.MCsr over random csrrw/csrrs/csrrc sequences (reg + imm)."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_mcsr_model as m  # noqa: E402

IMPLEMENTED = [m.MSTATUS, m.MISA, m.MIE, m.MTVEC, m.MSCRATCH, m.MEPC,
               m.MCAUSE, m.MTVAL, m.MIP, m.MVENDORID, m.MARCHID, m.MIMPID, m.MHARTID]
ALL_CHECK = IMPLEMENTED + [0x305, 0x000, 0xC00, 0x7FF]   # + a few unimplemented
FUNCT3 = [0b001, 0b010, 0b011, 0b101, 0b110, 0b111]      # RW/RS/RC reg + imm forms


async def reset(dut):
    dut.valid.value = 0
    dut.funct3.value = 0
    dut.csr_addr.value = 0
    dut.rs1.value = 0
    dut.zimm.value = 0
    dut.rd_addr.value = 0
    dut.rst.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def read_csr(dut, addr):
    dut.rd_addr.value = addr
    await Timer(1, units="ns")
    return int(dut.rd_data.value)


@cocotb.test()
async def test_mcsr(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    ref = m.MCsr()
    rng = random.Random(0x5E7C5B)

    # after reset, every CSR reads its fixed/zero value
    for a in ALL_CHECK:
        assert await read_csr(dut, a) == ref.read(a), f"reset read {a:03x}"

    for step in range(8000):
        valid = 1 if rng.random() < 0.9 else 0
        funct3 = rng.choice(FUNCT3)
        addr = rng.choice(IMPLEMENTED if rng.random() < 0.85 else [0x305, 0x000, 0xBFF, 0x7FF])
        rs1 = rng.getrandbits(32)
        zimm = rng.getrandbits(5)

        dut.valid.value = valid
        dut.funct3.value = funct3
        dut.csr_addr.value = addr
        dut.rs1.value = rs1
        dut.zimm.value = zimm
        await Timer(1, units="ns")

        # rd_val is the pre-write (old) value
        exp_old = ref.read(addr)
        assert int(dut.rd_val.value) == exp_old, \
            f"step {step}: rd_val {int(dut.rd_val.value):08x} != {exp_old:08x} (addr {addr:03x})"

        await RisingEdge(dut.clk)              # commit the write in RTL
        ref.step(valid, funct3, addr, rs1, zimm)  # commit in golden

        # full-state check: every CSR read-back matches the model
        for a in ALL_CHECK:
            got = await read_csr(dut, a)
            assert got == ref.read(a), \
                f"step {step}: CSR {a:03x} readback {got:08x} != {ref.read(a):08x}"

    dut._log.info("seth_mcsr verified bit-exact vs golden MCsr (8000 random CSR ops)")
