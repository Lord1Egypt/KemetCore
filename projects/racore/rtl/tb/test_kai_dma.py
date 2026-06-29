"""cocotb testbench for RaCore ra_kai_dma — end-to-end KAI-driven DMA vs golden."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ra_soc as g  # noqa: E402

SIZE = 1024


async def mmio_write(dut, off, val):
    dut.addr.value = off
    dut.wdata.value = val
    dut.wen.value = 1
    await RisingEdge(dut.clk)
    dut.wen.value = 0


async def mmio_read(dut, off):
    dut.addr.value = off
    dut.ren.value = 1
    await Timer(1, units="ns")
    v = int(dut.rdata.value)
    dut.ren.value = 0
    return v


async def preload(dut, data):
    for a, b in enumerate(data):
        dut.load_addr.value = a
        dut.load_data.value = b
        dut.load_en.value = 1
        await RisingEdge(dut.clk)
    dut.load_en.value = 0


@cocotb.test()
async def test_kai_dma(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    dut.wen.value = 0; dut.ren.value = 0; dut.load_en.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    rng = random.Random(0x0D3A)

    # ID register identifies the block
    assert await mmio_read(dut, g.KAI_ID) == ((0x0D << 24) | g.KAI_MAGIC)

    for _ in range(10):
        data = bytes(rng.getrandbits(8) for _ in range(SIZE))
        await preload(dut, data)
        length = rng.randint(1, 64)
        src = rng.randint(0, 200)
        dst = rng.randint(400, 700)
        # program the descriptor + launch like a host driver
        await mmio_write(dut, g.KAI_SRC, src)
        await mmio_write(dut, g.KAI_DST, dst)
        await mmio_write(dut, g.KAI_LEN, length)
        await mmio_write(dut, g.KAI_CTRL, g.CTRL_GO)
        # poll STATUS until DONE
        for _ in range(length + 50):
            st = await mmio_read(dut, g.KAI_STATUS)
            if st & g.STATUS_DONE:
                break
            await RisingEdge(dut.clk)
        assert st & g.STATUS_DONE, "DMA never signalled DONE"
        perf = await mmio_read(dut, g.KAI_PERF)
        assert perf >= length, f"PERF {perf} < len {length}"
        # data moved correctly (golden reference)
        scr = g.Scratchpad(SIZE); scr.mem[:] = bytearray(data)
        dma = g.Dma(scr); dma.copy(src, dst, length)
        for a in range(SIZE):
            dut.rd_addr.value = a
            await Timer(1, units="ns")
            assert int(dut.rd_data.value) == scr.mem[a], \
                f"byte {a}: len={length} src={src} dst={dst}"
    dut._log.info("ra_kai_dma verified end-to-end (KAI MMIO + DMA) vs golden")
