"""cocotb testbench for RaCore ra_kai_regs — bit-exact vs golden KaiRegs."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ra_soc as g  # noqa: E402

OFFS = [g.KAI_CAPS, g.KAI_CTRL, g.KAI_SRC, g.KAI_DST, g.KAI_LEN]
RDOFFS = [g.KAI_ID, g.KAI_CAPS, g.KAI_CTRL, g.KAI_STATUS, g.KAI_SRC, g.KAI_DST,
          g.KAI_LEN, g.KAI_PERF, 0x044]   # last = unmapped -> 0


async def idle(dut):
    dut.wen.value = 0
    dut.ren.value = 0
    dut.done.value = 0
    dut.err_in.value = 0
    await RisingEdge(dut.clk)


async def do_write(dut, ref, off, val):
    dut.addr.value = off
    dut.wdata.value = val
    dut.wen.value = 1
    await RisingEdge(dut.clk)        # commit
    dut.wen.value = 0
    ref.write(off, val)
    await Timer(1, units="ns")
    assert int(dut.go.value) == ref.go, f"go after write {off:#x}: {int(dut.go.value)}!={ref.go}"


async def do_finish(dut, ref, perf, err):
    dut.done.value = 1
    dut.perf.value = perf
    dut.err_in.value = err
    await RisingEdge(dut.clk)
    dut.done.value = 0
    ref.finish(perf, err)


async def check_all(dut, ref):
    await Timer(1, units="ns")
    for off in RDOFFS:
        dut.addr.value = off
        await Timer(1, units="ns")
        assert int(dut.rdata.value) == ref.read(off), \
            f"read {off:#x}: {int(dut.rdata.value):08x}!={ref.read(off):08x}"


@cocotb.test()
async def test_kai_regs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    await idle(dut)
    await idle(dut)
    dut.rst.value = 0
    ref = g.KaiRegs(block_id=0)
    await idle(dut); ref.idle()
    await check_all(dut, ref)

    rng = random.Random(0x4B41)
    for _ in range(3000):
        roll = rng.random()
        if roll < 0.6:
            off = rng.choice(OFFS)
            await do_write(dut, ref, off, rng.getrandbits(32))
        elif roll < 0.8:
            await do_finish(dut, ref, rng.getrandbits(32), rng.randint(0, 1))
        else:
            await idle(dut); ref.idle()
        await check_all(dut, ref)
    dut._log.info("ra_kai_regs verified bit-exact vs golden KaiRegs")
