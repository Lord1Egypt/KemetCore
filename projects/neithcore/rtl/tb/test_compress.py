"""cocotb testbench for NeithCore neith_compress — ML-KEM Compress_q, bit-exact
vs golden neith_mlkem.compress. Exhaustive over all Q ring coefficients."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as g  # noqa: E402

D = 10  # must match the RTL parameter default


@cocotb.test()
async def test_compress(dut):
    for x in range(g.Q):                     # exhaustive over [0, Q)
        dut.x.value = x
        await Timer(1, units="ns")
        exp = g.compress(x, D)
        got = int(dut.c.value)
        assert got == exp, f"compress({x}, {D}): got {got} exp {exp}"
        assert 0 <= got < (1 << D)
    dut._log.info(f"neith_compress verified bit-exact vs golden compress "
                  f"(exhaustive {g.Q} coefficients, D={D})")
