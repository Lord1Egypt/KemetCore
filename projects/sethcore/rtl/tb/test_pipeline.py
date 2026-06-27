"""cocotb testbench for seth_pipeline — the 5-stage interlocked RV32IM core.

Same methodology as the single-cycle core: assemble a program, preload it, run to
halt (ecall reaches WB), and compare the full final register file against the
golden ISA simulator. The interlock pipeline must reach the same architectural
state. Heavy on data hazards (back-to-back dependent instructions) and control
hazards (branches/jumps) to exercise stalls and flushes.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402


async def load_and_run(dut, words, max_cycles=60000):
    dut.rst.value = 1
    dut.load_en.value = 0
    dut.load_addr.value = 0
    dut.load_data.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    dut.load_en.value = 1
    for i, w in enumerate(words):
        dut.load_addr.value = i * 4
        dut.load_data.value = int(w) & 0xFFFFFFFF
        await RisingEdge(dut.clk)
    dut.load_en.value = 0
    cyc = 0
    while cyc < max_cycles:
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.halted.value) == 1:
            break
        cyc += 1
    assert cyc < max_cycles, "pipeline did not halt"


def regs(dut):
    return [int(dut.u_rf.regs[i].value) for i in range(32)]


async def run_prog(dut, prog):
    words = g.assemble(prog)
    await load_and_run(dut, words)
    cpu = g.Cpu()
    cpu.load(words)
    cpu.run()
    got = regs(dut)
    got[0] = 0
    for i in range(1, 32):
        assert got[i] == cpu.x[i], f"x{i}: pipeline {got[i]:08x} != golden {cpu.x[i]:08x}"


@cocotb.test()
async def test_sum_loop(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 3, 0, 11),
        "loop:", ("add", 1, 1, 2), ("addi", 2, 2, 1), ("blt", 2, 3, "loop"),
        ("ecall",)])
    dut._log.info("seth_pipeline: sum 1..10 matches golden")


@cocotb.test()
async def test_fibonacci(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 5, 0, 10),
        "fib:", ("add", 3, 1, 2), ("addi", 1, 2, 0), ("addi", 2, 3, 0),
        ("addi", 5, 5, -1), ("bne", 5, 0, "fib"), ("ecall",)])
    dut._log.info("seth_pipeline: fibonacci matches golden")


@cocotb.test()
async def test_dependent_chain(dut):
    """Back-to-back dependent ALU ops (every instruction reads the previous rd):
    maximal data-hazard stalling."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 1), ("addi", 1, 1, 1), ("add", 2, 1, 1), ("add", 3, 2, 2),
        ("sub", 4, 3, 1), ("mul", 5, 4, 3), ("and", 6, 5, 4), ("or", 7, 6, 5),
        ("xor", 8, 7, 6), ("sll", 9, 8, 1), ("srl", 10, 9, 1), ("ecall",)])
    dut._log.info("seth_pipeline: dependent chain (data hazards) matches golden")


@cocotb.test()
async def test_mem_and_jumps(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await run_prog(dut, [
        ("addi", 1, 0, 7), ("addi", 2, 0, -3 & 0xFFF), ("mul", 3, 1, 2),
        ("addi", 6, 0, 256), ("sw", 3, 0, 6), ("lw", 7, 0, 6),
        ("sb", 1, 8, 6), ("lbu", 8, 8, 6), ("jal", 9, "skip"),
        ("addi", 10, 0, 999),          # skipped by jal
        "skip:", ("lui", 11, 0xCAFE0000), ("ecall",)])
    dut._log.info("seth_pipeline: memory + jal control flow matches golden")


@cocotb.test()
async def test_branchy(dut):
    """Many forward branches that skip a dependent instruction — stresses branch
    flush interacting with data hazards on the fall-through path."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    prog = [("addi", r, 0, r) for r in range(1, 8)]
    for k in range(12):
        prog += [
            ("add", 9, 1, 2),                 # producer
            (("beq", "bne")[k & 1], 1, 2, f"s{k}"),   # taken-dependent branch
            ("addi", 9, 9, 100),              # data-hazard victim on fall-through
            f"s{k}:", ("sub", 1, 9, 3),
        ]
    prog.append(("ecall",))
    await run_prog(dut, prog)
    dut._log.info("seth_pipeline: branch-flush + hazard interaction matches golden")


@cocotb.test()
async def test_random_programs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0x9176E)
    iops = ["addi", "slti", "sltiu", "xori", "ori", "andi"]
    rops = ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and",
            "mul", "mulh", "mulhu", "div", "divu", "rem", "remu"]
    for _ in range(30):
        prog = [("addi", r, 0, rng.randint(-2048, 2047)) for r in range(1, 8)]
        for _ in range(rng.randint(15, 35)):
            if rng.random() < 0.5:
                prog.append((rng.choice(iops), rng.randint(1, 31),
                             rng.randint(1, 7), rng.randint(-2048, 2047)))
            else:
                prog.append((rng.choice(rops), rng.randint(1, 31),
                             rng.randint(1, 7), rng.randint(1, 7)))
        prog.append(("ecall",))
        await run_prog(dut, prog)
    dut._log.info("seth_pipeline: 30 randomised ALU/M programs match golden")
