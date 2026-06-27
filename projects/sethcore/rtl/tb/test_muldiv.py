"""cocotb testbench for SethCore seth_muldiv — bit-exact vs golden _muldiv."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402

# alu op -> golden funct3 (funct7 is 0x01 for the M-extension)
F3 = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7}


@cocotb.test()
async def test_muldiv(dut):
    cpu = g.Cpu()
    rng = random.Random(0)
    edge = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 2, 3, 7]
    cases = [(rng.randrange(1 << 32), rng.randrange(1 << 32)) for _ in range(400)]
    cases += [(e1, e2) for e1 in edge for e2 in edge]
    for av, bv in cases:
        for op, f3 in F3.items():
            dut.a.value = av
            dut.b.value = bv
            dut.op.value = op
            await Timer(1, units="ns")
            exp = cpu._muldiv(f3, av, bv)
            assert int(dut.y.value) == exp, f"op{op} a={av} b={bv}: {int(dut.y.value)}!={exp}"
    dut._log.info("seth_muldiv verified bit-exact vs golden")
