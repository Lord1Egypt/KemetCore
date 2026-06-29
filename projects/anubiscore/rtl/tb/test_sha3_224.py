"""cocotb testbench for AnubisCore sha3_224_core — bit-exact vs golden/hashlib.

Drives padded 1152-bit (144-byte) rate blocks with lanes pre-packed little-endian;
init=1 on the first block, 0 to chain. Digest = first 3.5 state lanes after the final
permutation, compared against hashlib.sha3_224 and the Python golden.
"""
import hashlib
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import anubis_hash as golden  # noqa: E402

RATE = 144  # bytes (1152 bits)


def pad(msg):
    padlen = RATE - (len(msg) % RATE)
    p = bytearray(padlen)
    p[0] ^= 0x06
    p[-1] ^= 0x80
    return bytes(msg) + bytes(p)


def pack_block(blk):
    """18 little-endian lanes packed into a 1152-bit integer (lane i at bits 64*i)."""
    val = 0
    for j in range(RATE // 8):
        lane = int.from_bytes(blk[8 * j:8 * j + 8], "little")
        val |= lane << (64 * j)
    return val


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.init.value = 0
    dut.block.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def absorb(dut, blk, init):
    dut.block.value = pack_block(blk)
    dut.init.value = 1 if init else 0
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    while True:
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break


async def sha3_224(dut, msg):
    padded = pad(msg)
    blocks = [padded[i:i + RATE] for i in range(0, len(padded), RATE)]
    for i, blk in enumerate(blocks):
        await absorb(dut, blk, init=(i == 0))
    val = int(dut.hash.value)             # {lane3[31:0],lane2,lane1,lane0}
    parts = [((val >> (64 * i)) & ((1 << 64) - 1)).to_bytes(8, "little")
             for i in range(3)]
    parts.append(((val >> 192) & 0xFFFFFFFF).to_bytes(4, "little"))  # low 32b of lane 3
    return b"".join(parts)                  # 28 bytes (224 bits)


@cocotb.test()
async def test_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    msgs = [b"", b"abc", b"a" * 143, b"a" * 144, b"a" * 145, b"a" * 288, b"a" * 400,
            b"hello kemet", os.urandom(100), os.urandom(216)]
    for m in msgs:
        got = await sha3_224(dut, m)
        assert got == hashlib.sha3_224(m).digest(), f"len {len(m)}: {got.hex()}"
        assert got == golden.sha3_224(m)
    dut._log.info(f"SHA3-224 RTL verified bit-exact on {len(msgs)} messages")
