"""cocotb testbench for SethCore seth_trap — M-mode trap vectoring + CSR updates,
bit-exact vs golden seth_trap_model (combinational)."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_trap_model as g  # noqa: E402


async def check(dut, pc, cause, is_int, mtvec, mstatus, mepc):
    dut.pc.value = pc
    dut.cause.value = cause
    dut.is_interrupt.value = is_int
    dut.mtvec.value = mtvec
    dut.mstatus.value = mstatus
    dut.mepc.value = mepc
    await Timer(1, units="ns")
    tgt, e_mepc, e_mcause, e_ms = g.trap_enter(pc, cause, is_int, mtvec, mstatus)
    r_tgt, r_ms = g.trap_return(mepc, mstatus)
    assert int(dut.enter_target.value) == tgt, f"enter_target {int(dut.enter_target.value):08x}!={tgt:08x}"
    assert int(dut.enter_mepc.value) == e_mepc
    assert int(dut.enter_mcause.value) == e_mcause, f"mcause {int(dut.enter_mcause.value):08x}!={e_mcause:08x}"
    assert int(dut.enter_mstatus.value) == e_ms, f"enter_mstatus {int(dut.enter_mstatus.value):08x}!={e_ms:08x}"
    assert int(dut.ret_target.value) == r_tgt
    assert int(dut.ret_mstatus.value) == r_ms, f"ret_mstatus {int(dut.ret_mstatus.value):08x}!={r_ms:08x}"


@cocotb.test()
async def test_trap(dut):
    # directed
    await check(dut, 0x1000, 2, 0, 0x80000000, (1 << 3) | (0b11 << 11), 0x1234)   # illegal instr, direct
    await check(dut, 0x2000, 7, 1, 0x80000001, 0, 0)                              # timer irq, vectored
    await check(dut, 0x3000, 11, 1, 0x80000000, (1 << 3), 0)                      # ext irq, direct (no vector)
    await check(dut, 0xFFFFFFFF, 0, 0, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)        # all-ones edge

    rng = random.Random(0x7BA9C0)
    for _ in range(12000):
        await check(dut, rng.getrandbits(32), rng.getrandbits(31), rng.randint(0, 1),
                    rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32))
    dut._log.info("seth_trap verified bit-exact vs golden (12004 vectors)")
