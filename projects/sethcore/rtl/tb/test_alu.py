"""cocotb testbench for SethCore seth_alu — bit-exact vs golden Cpu._alu_r."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as g  # noqa: E402

# alu op -> (funct7, funct3) for the golden R-type ALU
OPS = {0: (0x00, 0), 1: (0x20, 0), 2: (0x00, 1), 3: (0x00, 2), 4: (0x00, 3),
       5: (0x00, 4), 6: (0x00, 5), 7: (0x20, 5), 8: (0x00, 6), 9: (0x00, 7)}


@cocotb.test()
async def test_alu(dut):
    cpu = g.Cpu()
    rng = random.Random(0)
    edge = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 31, 32]
    for _ in range(400):
        a = rng.randrange(1 << 32)
        b = rng.randrange(1 << 32)
        for av, bv in [(a, b)] + [(e1, e2) for e1 in edge for e2 in edge[:3]]:
            for op, (f7, f3) in OPS.items():
                dut.a.value = av
                dut.b.value = bv
                dut.op.value = op
                await Timer(1, units="ns")
                exp = cpu._alu_r(f7, f3, av, bv)
                assert int(dut.y.value) == exp, f"op{op} a={av} b={bv}: {int(dut.y.value)}!={exp}"
    dut._log.info("seth_alu verified bit-exact vs golden")
