"""cocotb testbench for AnubisCore sha512_core — bit-exact vs hashlib.sha512.

Drives padded 1024-bit blocks (init=1 on the first, 0 to chain) and checks the final
512-bit digest against hashlib.sha512 (the authoritative oracle). Covers empty/short/
exact-block-boundary/multi-block and random messages.
"""
import hashlib
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


def pad(msg):
    ml = (8 * len(msg)) & ((1 << 128) - 1)
    m = bytearray(msg)
    m.append(0x80)
    while len(m) % 128 != 112:
        m.append(0x00)
    m += ml.to_bytes(16, "big")
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


async def hash512(dut, msg, alg):
    padded = pad(msg)
    blocks = [padded[i:i + 128] for i in range(0, len(padded), 128)]
    for i, blk in enumerate(blocks):
        await absorb(dut, blk, init=(i == 0), alg=alg)
    await RisingEdge(dut.clk)          # let the final H += vars settle
    return int(dut.hash.value)


@cocotb.test()
async def test_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    msgs = [b"", b"abc", b"a" * 111, b"a" * 112, b"a" * 128, b"a" * 239,
            b"hello kemet", os.urandom(200), os.urandom(400)]
    # SHA-512 (alg=0): full 512-bit digest
    for m in msgs:
        got = await hash512(dut, m, alg=0)
        exp = int.from_bytes(hashlib.sha512(m).digest(), "big")
        assert got == exp, f"sha512 len {len(m)}: got {got:0128x} != exp {exp:0128x}"
    # SHA-384 (alg=1): digest is the top 384 bits of the 512-bit state
    for m in msgs:
        full = await hash512(dut, m, alg=1)
        got = full >> 128
        exp = int.from_bytes(hashlib.sha384(m).digest(), "big")
        assert got == exp, f"sha384 len {len(m)}: got {got:096x} != exp {exp:096x}"
    dut._log.info(f"SHA-512 + SHA-384 RTL verified bit-exact on {len(msgs)} messages each")
