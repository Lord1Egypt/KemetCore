"""cocotb testbench for seth_pipeline_fwd — the 5-stage RV32IM core with forwarding.

Driven through seth_pipeline_cmp, which holds the interlock pipeline and the
forwarding pipeline side by side. For every program we:
  * load it into both cores, run each to halt (ecall reaches WB);
  * assert BOTH final register files equal the golden ISA simulator (forwarding is
    architecturally invariant);
  * record the halt cycle of each and assert the forwarding core is no slower, and
    strictly faster on the data-hazard-heavy programs — the whole point of forwarding.
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
    """Load `words` into both cores under reset, then run until both halt.
    Returns (il_cycles, fw_cycles): the cycle index at which each core halted."""
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

    il_cycles = fw_cycles = None
    cyc = 0
    while cyc < max_cycles:
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if il_cycles is None and int(dut.il_halted.value) == 1:
            il_cycles = cyc
        if fw_cycles is None and int(dut.fw_halted.value) == 1:
            fw_cycles = cyc
        if il_cycles is not None and fw_cycles is not None:
            break
        cyc += 1
    assert il_cycles is not None, "interlock pipeline did not halt"
    assert fw_cycles is not None, "forwarding pipeline did not halt"
    return il_cycles, fw_cycles


def regs(dut, inst):
    rf = getattr(dut, inst).u_rf
    return [int(rf.regs[i].value) for i in range(32)]


async def run_prog(dut, prog, expect_faster=False):
    words = g.assemble(prog)
    il_cycles, fw_cycles = await load_and_run(dut, words)

    cpu = g.Cpu()
    cpu.load(words)
    cpu.run()

    for inst, name in (("u_il", "interlock"), ("u_fw", "forwarding")):
        got = regs(dut, inst)
        got[0] = 0
        for i in range(1, 32):
            assert got[i] == cpu.x[i], \
                f"{name} x{i}: {got[i]:08x} != golden {cpu.x[i]:08x}"

    # Forwarding must never be slower than the broad interlock.
    assert fw_cycles <= il_cycles, \
        f"forwarding slower: fw={fw_cycles} il={il_cycles}"
    if expect_faster:
        assert fw_cycles < il_cycles, \
            f"forwarding expected strictly faster but fw={fw_cycles} il={il_cycles}"
    return il_cycles, fw_cycles


@cocotb.test()
async def test_sum_loop(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    il, fw = await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 3, 0, 11),
        "loop:", ("add", 1, 1, 2), ("addi", 2, 2, 1), ("blt", 2, 3, "loop"),
        ("ecall",)], expect_faster=True)
    dut._log.info(f"sum 1..10: forwarding {fw} cyc vs interlock {il} cyc, both == golden")


@cocotb.test()
async def test_fibonacci(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    il, fw = await run_prog(dut, [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 5, 0, 10),
        "fib:", ("add", 3, 1, 2), ("addi", 1, 2, 0), ("addi", 2, 3, 0),
        ("addi", 5, 5, -1), ("bne", 5, 0, "fib"), ("ecall",)], expect_faster=True)
    dut._log.info(f"fibonacci: forwarding {fw} cyc vs interlock {il} cyc, both == golden")


@cocotb.test()
async def test_dependent_chain(dut):
    """Back-to-back dependent ALU ops: maximal data hazards. With forwarding these
    issue with NO bubbles, so the forwarding core must be dramatically faster while
    reaching identical state."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    il, fw = await run_prog(dut, [
        ("addi", 1, 0, 1), ("addi", 1, 1, 1), ("add", 2, 1, 1), ("add", 3, 2, 2),
        ("sub", 4, 3, 1), ("mul", 5, 4, 3), ("and", 6, 5, 4), ("or", 7, 6, 5),
        ("xor", 8, 7, 6), ("sll", 9, 8, 1), ("srl", 10, 9, 1), ("ecall",)],
        expect_faster=True)
    dut._log.info(f"dependent chain: forwarding {fw} cyc vs interlock {il} cyc (no bubbles)")


@cocotb.test()
async def test_load_use(dut):
    """Load immediately feeding a dependent op — the one hazard forwarding cannot
    fully erase (1-cycle interlock). Still correct, and no slower than the broad
    interlock."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    il, fw = await run_prog(dut, [
        ("addi", 2, 0, 64), ("addi", 1, 0, 1234 & 0xFFF), ("sw", 1, 0, 2),
        ("lw", 5, 0, 2), ("add", 6, 5, 5),       # load-use: lw -> add
        ("lw", 7, 0, 2), ("addi", 8, 7, 1),      # load-use: lw -> addi
        ("ecall",)])
    dut._log.info(f"load-use: forwarding {fw} cyc vs interlock {il} cyc, both == golden")


@cocotb.test()
async def test_mem_and_jumps(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    il, fw = await run_prog(dut, [
        ("addi", 1, 0, 7), ("addi", 2, 0, -3 & 0xFFF), ("mul", 3, 1, 2),
        ("addi", 6, 0, 256), ("sw", 3, 0, 6), ("lw", 7, 0, 6),
        ("sb", 1, 8, 6), ("lbu", 8, 8, 6), ("jal", 9, "skip"),
        ("addi", 10, 0, 999),          # skipped by jal
        "skip:", ("lui", 11, 0xCAFE0000), ("ecall",)])
    dut._log.info(f"mem + jumps: forwarding {fw} cyc vs interlock {il} cyc, both == golden")


@cocotb.test()
async def test_branchy(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    prog = [("addi", r, 0, r) for r in range(1, 8)]
    for k in range(12):
        prog += [
            ("add", 9, 1, 2),
            (("beq", "bne")[k & 1], 1, 2, f"s{k}"),
            ("addi", 9, 9, 100),
            f"s{k}:", ("sub", 1, 9, 3),
        ]
    prog.append(("ecall",))
    il, fw = await run_prog(dut, prog, expect_faster=True)
    dut._log.info(f"branchy: forwarding {fw} cyc vs interlock {il} cyc, both == golden")


@cocotb.test()
async def test_random_programs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0x9176E)
    iops = ["addi", "slti", "sltiu", "xori", "ori", "andi"]
    rops = ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and",
            "mul", "mulh", "mulhu", "div", "divu", "rem", "remu"]
    total_il = total_fw = 0
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
        il, fw = await run_prog(dut, prog)
        total_il += il
        total_fw += fw
    assert total_fw < total_il, f"forwarding not faster overall: {total_fw} vs {total_il}"
    dut._log.info(f"30 random programs: forwarding {total_fw} cyc vs interlock {total_il} cyc total")
