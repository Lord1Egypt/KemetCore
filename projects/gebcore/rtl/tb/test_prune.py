"""cocotb testbench for GebCore geb_prune — bit-exact vs golden prune_group."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import geb_sparse as golden  # noqa: E402


def f2b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


async def check(dut, bits4):
    dut.w0.value, dut.w1.value, dut.w2.value, dut.w3.value = bits4
    await Timer(1, units="ns")
    mask, kept = golden.prune_group(bits4)
    assert int(dut.keep_mask.value) == mask, \
        f"mask {bits4}: {int(dut.keep_mask.value):04b}!={mask:04b}"
    assert int(dut.idx0.value) == kept[0][0] and int(dut.val0.value) == kept[0][1], \
        f"kept0 {bits4}: ({int(dut.idx0.value)},{int(dut.val0.value):08x}) != {kept[0]}"
    assert int(dut.idx1.value) == kept[1][0] and int(dut.val1.value) == kept[1][1], \
        f"kept1 {bits4}: ({int(dut.idx1.value)},{int(dut.val1.value):08x}) != {kept[1]}"


@cocotb.test()
async def test_prune(dut):
    # directed: distinct magnitudes, ties, zeros, negatives
    directed = [
        [f2b(1.0), f2b(2.0), f2b(3.0), f2b(4.0)],
        [f2b(-4.0), f2b(1.0), f2b(-2.0), f2b(0.5)],
        [f2b(0.0), f2b(0.0), f2b(0.0), f2b(0.0)],
        [f2b(5.0), f2b(-5.0), f2b(5.0), f2b(1.0)],   # magnitude ties -> lower lane
        [f2b(1e30), f2b(1e-30), f2b(-1e30), f2b(2.0)],
    ]
    for b in directed:
        await check(dut, b)
    # random fp32 groups
    for _ in range(6000):
        await check(dut, [f2b(random.uniform(-1e3, 1e3)) for _ in range(4)])
    # random raw bit patterns (incl subnormal/inf/nan — selection still deterministic)
    for _ in range(4000):
        await check(dut, [random.getrandbits(32) for _ in range(4)])
    dut._log.info("geb_prune verified bit-exact vs golden prune_group")
