"""cocotb testbench for PtahConv ptah_conv2d — bit-exact vs golden conv2d_seq."""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ptah_conv as golden  # noqa: E402


def f2b(x):
    return int(np.frombuffer(struct.pack("<f", np.float32(x)), np.uint32)[0])


async def preload(dut, en, addr, data, vals):
    for i, v in enumerate(vals):
        getattr(dut, addr).value = i
        getattr(dut, data).value = v
        getattr(dut, en).value = 1
        await RisingEdge(dut.clk)
    getattr(dut, en).value = 0


async def run_conv(dut, xb, wb, Cin, H, W, Cout, KH, KW, stride, pad):
    await preload(dut, "ld_in_en", "ld_in_addr", "ld_in_data", xb)
    await preload(dut, "ld_w_en", "ld_w_addr", "ld_w_data", wb)
    for f in ("Cin", "H", "W", "Cout", "KH", "KW", "stride", "pad"):
        getattr(dut, f).value = locals()[f]
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    OH = (H + 2 * pad - KH) // stride + 1
    OW = (W + 2 * pad - KW) // stride + 1
    budget = Cout * OH * OW * (Cin * KH * KW + 4) + 100
    for _ in range(budget):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "conv did not finish"
    return Cout * OH * OW


@cocotb.test()
async def test_conv2d(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    dut.ld_in_en.value = 0; dut.ld_w_en.value = 0; dut.start.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    rng = random.Random(0xC04D)

    cases = [
        (1, 4, 4, 1, 3, 3, 1, 0),     # valid 3x3
        (2, 4, 4, 3, 3, 3, 1, 1),     # same-pad, multi-channel
        (1, 5, 5, 2, 3, 3, 2, 0),     # strided
        (3, 4, 4, 2, 1, 1, 1, 0),     # 1x1 (pointwise)
        (2, 6, 6, 2, 3, 3, 1, 1),
    ]
    for (Cin, H, W, Cout, KH, KW, stride, pad) in cases:
        x = rng.gauss
        xb = [f2b(rng.gauss(0, 1)) for _ in range(Cin * H * W)]
        wb = [f2b(rng.gauss(0, 1)) for _ in range(Cout * Cin * KH * KW)]
        n = await run_conv(dut, xb, wb, Cin, H, W, Cout, KH, KW, stride, pad)
        exp = golden.conv2d_seq(xb, wb, Cin, H, W, Cout, KH, KW, stride, pad)
        assert len(exp) == n
        for i in range(n):
            dut.rd_addr.value = i
            await Timer(1, units="ns")
            assert int(dut.rd_data.value) == exp[i], \
                f"cfg Cin{Cin}H{H}W{W}Co{Cout}K{KH}s{stride}p{pad} out[{i}]: " \
                f"{int(dut.rd_data.value):08x}!={exp[i]:08x}"

    # --- P0.4 hardening proof: a stray preload asserted DURING a convolution must
    # be ignored (IDLE-gated), so it cannot corrupt imem/wmem mid-flight. ---
    Cin, H, W, Cout, KH, KW, stride, pad = 1, 4, 4, 1, 3, 3, 1, 0
    xb = [f2b(rng.gauss(0, 1)) for _ in range(Cin * H * W)]
    wb = [f2b(rng.gauss(0, 1)) for _ in range(Cout * Cin * KH * KW)]
    exp = golden.conv2d_seq(xb, wb, Cin, H, W, Cout, KH, KW, stride, pad)
    await preload(dut, "ld_in_en", "ld_in_addr", "ld_in_data", xb)
    await preload(dut, "ld_w_en", "ld_w_addr", "ld_w_data", wb)
    for fld in ("Cin", "H", "W", "Cout", "KH", "KW", "stride", "pad"):
        getattr(dut, fld).value = locals()[fld]
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    # while BUSY, hammer imem[0]/wmem[0] with garbage — the gate must drop these
    injected = 0
    for _ in range(Cin * KH * KW + 6):
        await RisingEdge(dut.clk)
        if int(dut.busy.value) == 1:
            dut.ld_in_en.value = 1; dut.ld_in_addr.value = 0; dut.ld_in_data.value = 0xDEADBEEF
            dut.ld_w_en.value = 1;  dut.ld_w_addr.value = 0;  dut.ld_w_data.value = 0xDEADBEEF
            injected += 1
        if int(dut.done.value) == 1:
            break
    dut.ld_in_en.value = 0; dut.ld_w_en.value = 0
    while int(dut.done.value) == 0:
        await RisingEdge(dut.clk)
    assert injected > 0, "test bug: never injected a load during busy"
    n = Cout * ((H + 2*pad - KH)//stride + 1) * ((W + 2*pad - KW)//stride + 1)
    for i in range(n):
        dut.rd_addr.value = i
        await Timer(1, units="ns")
        assert int(dut.rd_data.value) == exp[i], \
            f"load-during-busy corrupted out[{i}]: {int(dut.rd_data.value):08x}!={exp[i]:08x}"
    dut._log.info(f"ptah_conv2d load-gate proof OK ({injected} mid-busy loads dropped)")

    dut._log.info("ptah_conv2d verified bit-exact vs golden conv2d_seq")
