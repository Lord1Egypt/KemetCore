"""cocotb testbench for atum_vregfile — the AtumCore vector register file.

Drives random writes and dual reads, comparing against a Python model: synchronous
write (commits on the rising edge), asynchronous reads over committed state, and a
synchronous reset that clears all registers.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

NREGS = 32
VLMAX = 8
ELEN = 32
VLEN = VLMAX * ELEN
VMASK = (1 << VLEN) - 1


@cocotb.test()
async def test_random_rw(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0x7E6151E)
    model = [0] * NREGS

    # synchronous reset
    dut.rst.value = 1
    dut.we.value = 0
    dut.waddr.value = 0
    dut.wdata.value = 0
    dut.raddr1.value = 0
    dut.raddr2.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    for r in range(NREGS):
        dut.raddr1.value = r
        await Timer(1, units="ns")
        assert int(dut.rdata1.value) == 0, f"v{r} not cleared by reset"

    for _ in range(4000):
        we = rng.randint(0, 1)
        waddr = rng.randint(0, NREGS - 1)
        wdata = rng.getrandbits(VLEN)
        ra1 = rng.randint(0, NREGS - 1)
        ra2 = rng.randint(0, NREGS - 1)
        dut.we.value = we
        dut.waddr.value = waddr
        dut.wdata.value = wdata
        dut.raddr1.value = ra1
        dut.raddr2.value = ra2
        await RisingEdge(dut.clk)
        if we:
            model[waddr] = wdata
        await Timer(1, units="ns")
        assert int(dut.rdata1.value) == model[ra1], f"rdata1 v{ra1}"
        assert int(dut.rdata2.value) == model[ra2], f"rdata2 v{ra2}"
    dut._log.info("atum_vregfile: 4000 random rw cycles + reset match model")
