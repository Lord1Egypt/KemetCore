"""cocotb testbench for AnubisCore sha256_core — bit-exact vs golden/hashlib.

Drives padded 512-bit blocks (init=1 on the first, 0 to chain) and checks the
final digest against hashlib (which the Python golden matches exactly).
"""
import hashlib
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import anubis_hash as golden  # noqa: E402


def pad(msg):
    ml = (8 * len(msg)) & ((1 << 64) - 1)
    m = bytearray(msg)
    m.append(0x80)
    while len(m) % 64 != 56:
        m.append(0x00)
    m += ml.to_bytes(8, "big")
    return bytes(m)


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.init.value = 0
    dut.alg.value = 0
    dut.block.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def absorb(dut, blk_bytes, init, alg):
    dut.block.value = int.from_bytes(blk_bytes, "big")
    dut.init.value = 1 if init else 0
    dut.alg.value = alg
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    while True:
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break


async def sha256(dut, msg, alg=0):
    padded = pad(msg)
    blocks = [padded[i:i + 64] for i in range(0, len(padded), 64)]
    for i, blk in enumerate(blocks):
        await absorb(dut, blk, init=(i == 0), alg=alg)
    await RisingEdge(dut.clk)          # let the final H += vars settle
    return int(dut.hash.value)


@cocotb.test()
async def test_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    msgs = [b"", b"abc", b"a" * 55, b"a" * 56, b"a" * 64, b"a" * 119,
            b"hello kemet", os.urandom(100), os.urandom(200)]
    # SHA-256 (alg=0): full 256-bit digest, also cross-checked vs the from-scratch golden
    for m in msgs:
        got = await sha256(dut, m, alg=0)
        exp = int.from_bytes(hashlib.sha256(m).digest(), "big")
        assert got == exp, f"sha256 len {len(m)}: got {got:064x} != exp {exp:064x}"
        assert got == int.from_bytes(golden.sha256(m), "big")
    # SHA-224 (alg=1): digest is the top 224 bits of the 256-bit state
    for m in msgs:
        got = (await sha256(dut, m, alg=1)) >> 32
        exp = int.from_bytes(hashlib.sha224(m).digest(), "big")
        assert got == exp, f"sha224 len {len(m)}: got {got:056x} != exp {exp:056x}"
    dut._log.info(f"SHA-256 + SHA-224 RTL verified bit-exact on {len(msgs)} messages each")
