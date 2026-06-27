"""cocotb testbench for seth_core — the integrated single-cycle RV32IM core.

Each program is assembled, preloaded into the core's memory, run to completion
(halt on ecall), and the full final register file is compared against the golden
ISA simulator. Also runs randomised ALU/branch programs for breadth.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


async def load_and_run(dut, words, max_cycles=20000):
    # reset
    dut.rst.value = 1
    dut.load_en.value = 0
    dut.load_addr.value = 0
    dut.load_data.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    # preload program (word-addressed)
    dut.load_en.value = 1
    for i, w in enumerate(words):
        dut.load_addr.value = i * 4
        dut.load_data.value = int(w) & 0xFFFFFFFF
        await RisingEdge(dut.clk)
    dut.load_en.value = 0
    # run until halted
    cyc = 0
    while cyc < max_cycles:
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.halted.value) == 1:
            break
        cyc += 1
    assert cyc < max_cycles, "core did not halt"


def regs(dut):
    return [int(dut.u_rf.regs[i].value) for i in range(32)]


async def run_prog(dut, prog):
    words = g.assemble(prog)
    await load_and_run(dut, words)
    cpu = g.Cpu()
    cpu.load(words)
    cpu.run()
    got = regs(dut)
    got[0] = 0  # x0 reads as 0 regardless of the unwritten storage slot
    for i in range(1, 32):
        assert got[i] == cpu.x[i], (
            f"x{i}: core {got[i]:08x} != golden {cpu.x[i]:08x}")


@cocotb.test()
async def test_sum_loop(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 3, 0, 11),
        "loop:", ("add", 1, 1, 2), ("addi", 2, 2, 1), ("blt", 2, 3, "loop"),
        ("ecall",)])
    dut._log.info("seth_core: sum 1..10 program matches golden")


@cocotb.test()
async def test_fibonacci(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 5, 0, 10),
        "fib:", ("add", 3, 1, 2), ("addi", 1, 2, 0), ("addi", 2, 3, 0),
        ("addi", 5, 5, -1), ("bne", 5, 0, "fib"), ("ecall",)])
    dut._log.info("seth_core: fibonacci program matches golden")


@cocotb.test()
async def test_mul_div_and_memory(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 7), ("addi", 2, 0, -3 & 0xFFF),
        ("mul", 3, 1, 2), ("div", 4, 1, 2), ("rem", 5, 1, 2),
        ("addi", 6, 0, 256), ("sw", 3, 0, 6), ("lw", 7, 0, 6),
        ("sh", 1, 8, 6), ("lhu", 8, 8, 6), ("sb", 2, 12, 6), ("lb", 9, 12, 6),
        ("lui", 10, 0xABCDE000), ("auipc", 11, 0x1000),
        ("ecall",)])
    dut._log.info("seth_core: mul/div + load/store + lui/auipc program matches golden")


@cocotb.test()
async def test_random_programs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0x5E7C0DE)
    iops = ["addi", "slti", "sltiu", "xori", "ori", "andi"]
    rops = ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and",
            "mul", "mulh", "mulhu", "div", "divu", "rem", "remu"]
    for _ in range(40):
        prog = [("addi", r, 0, rng.randint(-2048, 2047)) for r in range(1, 8)]
        for _ in range(rng.randint(10, 30)):
            if rng.random() < 0.5:
                prog.append((rng.choice(iops), rng.randint(1, 31),
                             rng.randint(1, 7), rng.randint(-2048, 2047)))
            else:
                prog.append((rng.choice(rops), rng.randint(1, 31),
                             rng.randint(1, 7), rng.randint(1, 7)))
        prog.append(("ecall",))
        await run_prog(dut, prog)
    dut._log.info("seth_core: 40 randomised ALU/M programs match golden")
