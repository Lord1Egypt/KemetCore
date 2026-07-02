"""cocotb testbench for RaCore ra_scratchpad — byte-enabled SRAM, bit-exact vs
golden Scratchpad.write_word / read_word."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ra_soc as g  # noqa: E402

DEPTH = 256
SIZE = DEPTH * 4


async def write_word(dut, waddr, be, wdata):
    dut.en.value = 1
    dut.we.value = 1
    dut.be.value = be
    dut.addr.value = waddr
    dut.wdata.value = wdata
    await RisingEdge(dut.clk)
    dut.en.value = 0
    dut.we.value = 0


async def read_word(dut, raddr):
    dut.en.value = 1
    dut.we.value = 0
    dut.addr.value = raddr
    await RisingEdge(dut.clk)          # this edge latches mem[raddr] into rdata
    dut.en.value = 0
    await Timer(1, units="ns")         # let the NBA update to rdata settle
    return int(dut.rdata.value)


@cocotb.test()
async def test_scratchpad(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.en.value = 0
    dut.we.value = 0
    dut.be.value = 0
    await RisingEdge(dut.clk)

    rng = random.Random(0x5C24)
    scr = g.Scratchpad(SIZE)

    # --- full-word preload then verify every word reads back ---
    for a in range(DEPTH):
        wd = rng.getrandbits(32)
        await write_word(dut, a, 0xF, wd)
        scr.write_word(a, 0xF, wd)
    for a in range(DEPTH):
        got = await read_word(dut, a)
        assert got == scr.read_word(a), \
            f"preload readback @ {a}: {got:#010x} != {scr.read_word(a):#010x}"

    # --- random masked (partial-word) writes interleaved with reads ---
    for _ in range(400):
        a = rng.randint(0, DEPTH - 1)
        be = rng.randint(0, 0xF)
        wd = rng.getrandbits(32)
        await write_word(dut, a, be, wd)
        scr.write_word(a, be, wd)
        got = await read_word(dut, a)
        assert got == scr.read_word(a), \
            f"masked write a={a} be={be:#x} wd={wd:#010x}: " \
            f"{got:#010x} != {scr.read_word(a):#010x}"

    # --- be=0 write must be a no-op (data preserved) ---
    a = rng.randint(0, DEPTH - 1)
    before = await read_word(dut, a)
    await write_word(dut, a, 0x0, 0xDEADBEEF)
    scr.write_word(a, 0x0, 0xDEADBEEF)
    after = await read_word(dut, a)
    assert after == before == scr.read_word(a), "be=0 write was not a no-op"

    dut._log.info("ra_scratchpad verified bit-exact vs golden Scratchpad "
                  "(full-word + per-byte masked writes)")
