"""cocotb testbench for AnubisCore shake128_xof_core — bit-exact vs hashlib.shake_128.

Absorbs padded 1344-bit (168-byte) rate blocks (SHAKE domain pad 0x1F, host-side),
then squeezes as many 168-byte output blocks as needed for the requested length.
"""
import hashlib
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

RATE = 168  # bytes (1344 bits)


def pad(msg):
    padlen = RATE - (len(msg) % RATE)
    p = bytearray(padlen)
    p[0] ^= 0x1F          # SHAKE domain separation
    p[-1] ^= 0x80
    return bytes(msg) + bytes(p)


def pack(blk):
    val = 0
    for j in range(RATE // 8):
        val |= int.from_bytes(blk[8 * j:8 * j + 8], "little") << (64 * j)
    return val


def unpack(val):
    return b"".join(((val >> (64 * j)) & ((1 << 64) - 1)).to_bytes(8, "little")
                    for j in range(RATE // 8))


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.init.value = 0
    dut.squeeze.value = 0
    dut.block.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def absorb(dut, blk, init):
    dut.block.value = pack(blk)
    dut.init.value = 1 if init else 0
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    dut.init.value = 0
    while True:
        await RisingEdge(dut.clk)
        if dut.absorb_done.value == 1:
            break


async def squeeze_once(dut):
    dut.squeeze.value = 1
    await RisingEdge(dut.clk)
    dut.squeeze.value = 0
    while True:
        await RisingEdge(dut.clk)
        if dut.squeeze_done.value == 1:
            break


async def shake(dut, msg, nbytes):
    padded = pad(msg)
    blocks = [padded[i:i + RATE] for i in range(0, len(padded), RATE)]
    for i, blk in enumerate(blocks):
        await absorb(dut, blk, init=(i == 0))
    out = bytearray()
    out += unpack(int(dut.out_block.value))      # first squeeze block (no extra perm)
    while len(out) < nbytes:
        await squeeze_once(dut)
        out += unpack(int(dut.out_block.value))
    return bytes(out[:nbytes])


@cocotb.test()
async def test_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    cases = [
        (b"", 32), (b"abc", 32), (b"abc", 64),
        (b"a" * 167, 16), (b"a" * 168, 168), (b"a" * 169, 200),
        (b"hello kemet", 100), (b"The quick brown fox", 512),
        (os.urandom(50), 400), (os.urandom(300), 333),
    ]
    for msg, n in cases:
        got = await shake(dut, msg, n)
        ref = hashlib.shake_128(msg).digest(n)
        assert got == ref, f"len(msg)={len(msg)} n={n}: {got[:8].hex()} != {ref[:8].hex()}"
    dut._log.info(f"shake128_xof_core verified bit-exact vs hashlib on {len(cases)} cases")
