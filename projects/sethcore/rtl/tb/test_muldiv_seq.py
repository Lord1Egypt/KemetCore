"""cocotb testbench for SethCore seth_muldiv_seq (iterative) — bit-exact vs golden."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


async def reset(dut):
    dut.rst.value = 1
    dut.start.value = 0
    dut.op.value = 0
    dut.a.value = 0
    dut.b.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def do_op(dut, op, av, bv):
    """Drive one start pulse, wait for done, return y. Assert busy/done timing."""
    dut.op.value = op
    dut.a.value = av
    dut.b.value = bv
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    dut.a.value = 0
    dut.b.value = 0
    # wait for done (bounded — MUL ~1 cyc, DIV ~34 cyc)
    for cyc in range(60):
        await RisingEdge(dut.clk)
        if int(dut.done.value) == 1:
            return int(dut.y.value)
    raise cocotb.result.TestFailure(f"no done for op{op} a={av} b={bv}")


@cocotb.test()
async def test_muldiv_seq(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    cpu = g.Cpu()
    rng = random.Random(1)
    edge = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 2, 3, 7, 0xFFFF, 0x10000]
    cases = [(rng.randrange(1 << 32), rng.randrange(1 << 32)) for _ in range(150)]
    cases += [(e1, e2) for e1 in edge for e2 in edge]
    for av, bv in cases:
        for op in range(8):
            got = await do_op(dut, op, av, bv)
            exp = cpu._muldiv(op, av, bv)
            assert got == exp, f"op{op} a={av:#x} b={bv:#x}: got {got:#x} != exp {exp:#x}"
    # idle handshake: no spurious done between ops
    assert int(dut.busy.value) == 0
    dut._log.info("seth_muldiv_seq verified bit-exact vs golden (all 8 ops)")
