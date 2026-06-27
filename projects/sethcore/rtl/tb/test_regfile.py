"""cocotb testbench for seth_regfile — checked against a Python reference model.

Synchronous write / asynchronous read, x0 hardwired to 0. Verifies: initial
write-then-read of all 31 writable registers, x0 reads as 0 even after a write,
dual-port reads, and a long randomised stream of write/read cycles tracked by a
reference model.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))


class RefRegfile:
    """Reference: 32 regs, x0 == 0, write commits at the clock edge."""
    def __init__(self):
        self.x = [0] * 32

    def commit(self, we, waddr, wdata):
        if we and waddr != 0:
            self.x[waddr] = wdata & 0xFFFFFFFF

    def read(self, addr):
        return 0 if addr == 0 else self.x[addr]


async def settle():
    await Timer(1, units="ns")


async def do_read(dut, ref, r1, r2):
    dut.raddr1.value = r1
    dut.raddr2.value = r2
    await settle()
    assert int(dut.rdata1.value) == ref.read(r1), f"rdata1 x{r1}"
    assert int(dut.rdata2.value) == ref.read(r2), f"rdata2 x{r2}"


async def do_write(dut, ref, we, waddr, wdata):
    dut.we.value = we
    dut.waddr.value = waddr
    dut.wdata.value = wdata
    await RisingEdge(dut.clk)
    ref.commit(we, waddr, wdata)
    await settle()                      # let async reads re-evaluate after the edge


@cocotb.test()
async def test_write_then_read_all(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    ref = RefRegfile()
    dut.we.value = 0; dut.waddr.value = 0; dut.wdata.value = 0
    dut.raddr1.value = 0; dut.raddr2.value = 0
    await RisingEdge(dut.clk)
    for i in range(1, 32):
        await do_write(dut, ref, 1, i, 0xCAFE0000 | i)
    for i in range(1, 32):
        await do_read(dut, ref, i, (i * 7) % 32)
    dut._log.info("seth_regfile: all 31 writable registers write/read verified")


@cocotb.test()
async def test_x0_hardwired(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    ref = RefRegfile()
    await do_write(dut, ref, 1, 0, 0xDEADBEEF)     # write to x0 -> ignored
    await do_read(dut, ref, 0, 0)
    assert int(dut.rdata1.value) == 0 and int(dut.rdata2.value) == 0
    dut._log.info("seth_regfile: x0 stays 0 after a write")


@cocotb.test()
async def test_random_stream(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    ref = RefRegfile()
    rng = random.Random(0x5E7DEAD)
    # prime every register so reads compare against known data
    for i in range(1, 32):
        await do_write(dut, ref, 1, i, rng.getrandbits(32))
    n = 0
    for _ in range(20000):
        await do_read(dut, ref, rng.randrange(32), rng.randrange(32))
        await do_write(dut, ref, rng.randint(0, 1), rng.randrange(32), rng.getrandbits(32))
        n += 1
    dut._log.info(f"seth_regfile: {n} randomised write/read cycles verified")
