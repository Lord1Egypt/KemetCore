"""cocotb testbench for NeithCore neith_decompress — ML-KEM Decompress_q,
bit-exact vs golden neith_mlkem.decompress. Exhaustive over all 2^D inputs."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as g  # noqa: E402

D = 10  # must match the RTL parameter default


@cocotb.test()
async def test_decompress(dut):
    for y in range(1 << D):
        dut.y.value = y
        await Timer(1, units="ns")
        exp = g.decompress(y, D)
        got = int(dut.coeff.value)
        assert got == exp, f"decompress({y}, {D}): got {got} exp {exp}"
        assert 0 <= got < g.Q, f"decompress({y}) = {got} out of ring [0,{g.Q})"
    dut._log.info(f"neith_decompress verified bit-exact vs golden decompress "
                  f"(exhaustive {1 << D} inputs, D={D})")
