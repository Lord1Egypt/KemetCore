"""cocotb testbench for RaCore ra_dma — bit-exact vs golden Dma over a scratchpad."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ra_soc as g  # noqa: E402

SIZE = 1024


async def preload(dut, data):
    for addr, b in enumerate(data):
        dut.load_addr.value = addr
        dut.load_data.value = b
        dut.load_en.value = 1
        await RisingEdge(dut.clk)
    dut.load_en.value = 0


async def run_copy(dut, src, dst, rows, row_bytes, ss, ds):
    dut.src.value = src
    dut.dst.value = dst
    dut.rows.value = rows
    dut.row_bytes.value = row_bytes
    dut.src_stride.value = ss
    dut.dst_stride.value = ds
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for _ in range(rows * row_bytes + 50):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "dma did not finish"


async def read_all(dut):
    out = bytearray(SIZE)
    for a in range(SIZE):
        dut.rd_addr.value = a
        await Timer(1, units="ns")
        out[a] = int(dut.rd_data.value)
    return out


@cocotb.test()
async def test_dma(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    dut.load_en.value = 0
    dut.start.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    rng = random.Random(0xD3A)

    # --- 1D copies ---
    for _ in range(8):
        data = bytes(rng.getrandbits(8) for _ in range(SIZE))
        await preload(dut, data)
        length = rng.randint(1, 64)
        src = rng.randint(0, 200)
        dst = rng.randint(400, 700)              # non-overlapping with src run
        await run_copy(dut, src, dst, 1, length, length, length)
        scr = g.Scratchpad(SIZE); scr.mem[:] = bytearray(data)
        dma = g.Dma(scr); dma.copy(src, dst, length)
        got = await read_all(dut)
        assert bytes(got) == bytes(scr.mem), f"1D len={length} src={src} dst={dst}"

    # --- 2D / strided copies ---
    for _ in range(8):
        data = bytes(rng.getrandbits(8) for _ in range(SIZE))
        await preload(dut, data)
        rows = rng.randint(1, 6)
        row_bytes = rng.randint(1, 16)
        ss = row_bytes + rng.randint(0, 8)
        ds = row_bytes + rng.randint(0, 8)
        src = rng.randint(0, 100)
        dst = rng.randint(500, 600)
        await run_copy(dut, src, dst, rows, row_bytes, ss, ds)
        scr = g.Scratchpad(SIZE); scr.mem[:] = bytearray(data)
        dma = g.Dma(scr); dma.copy_2d(src, dst, rows, row_bytes, ss, ds)
        got = await read_all(dut)
        assert bytes(got) == bytes(scr.mem), \
            f"2D rows={rows} rb={row_bytes} ss={ss} ds={ds} src={src} dst={dst}"
    dut._log.info("ra_dma verified bit-exact vs golden Dma (1D + 2D)")
