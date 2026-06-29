"""cocotb testbench for AnubisCore hmac_sha512_core — bit-exact vs stdlib hmac.

The core absorbs the ipad key block itself, then requests the remaining inner
message blocks (SHA-256 padding of (ipad||msg) minus its first 128 bytes, whose
length field accounts for the 64-byte prefix). The outer hash is fully internal.
Compared against the stdlib hmac/hashlib (no from-scratch sha512 golden exists,
mirroring sha512_core's hashlib-oracle verification).
"""
import hashlib
import hmac as _hmac
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

BLOCK = 128  # SHA-512 block size (bytes)


def sha512_pad(msg):
    L = len(msg) * 8
    m = bytearray(msg)
    m.append(0x80)
    while len(m) % 128 != 112:
        m.append(0x00)
    m += L.to_bytes(16, "big")
    return bytes(m)


def inner_blocks(msg):
    """Inner message blocks after the ipad block: SHA-pad(ipad||msg)[64:].

    The ipad block content is irrelevant here (the core builds it); only the
    64-byte prefix length matters, so a zero placeholder prefix is used."""
    full = sha512_pad(b"\x00" * BLOCK + bytes(msg))
    tail = full[BLOCK:]
    return [tail[i:i + 128] for i in range(0, len(tail), 128)]


def keypad(key):
    if len(key) > BLOCK:
        key = hashlib.sha512(key).digest()
    return key + b"\x00" * (BLOCK - len(key))


async def reset(dut):
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.key.value = 0
    dut.blk.value = 0
    dut.blk_valid.value = 0
    dut.blk_last.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def hmac_run(dut, key, msg):
    kp = keypad(key)
    dut.key.value = int.from_bytes(kp, "big")
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    blocks = inner_blocks(msg)
    bi = 0
    # Feed inner blocks when the core requests them, then wait for done.
    for _ in range(200000):
        await RisingEdge(dut.clk)
        if bi < len(blocks) and dut.need_block.value == 1:
            dut.blk.value = int.from_bytes(blocks[bi], "big")
            dut.blk_valid.value = 1
            dut.blk_last.value = 1 if bi == len(blocks) - 1 else 0
            bi += 1
            await RisingEdge(dut.clk)
            dut.blk_valid.value = 0
            dut.blk_last.value = 0
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "HMAC did not complete"
    val = int(dut.mac.value)
    return val.to_bytes(64, "big")


@cocotb.test()
async def test_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    cases = [
        (b"key", b"The quick brown fox jumps over the lazy dog"),
        (b"", b""),
        (b"a" * 64, b"abc"),
        (b"Jefe", b"what do ya want for nothing?"),
        (b"k", b"a" * 111),    # inner tail spans exactly the boundary
        (b"k", b"a" * 112),    # forces an extra inner block
        (b"k", b"a" * 200),
        (b"x" * 200, b"long key gets hashed first"),  # key > block size
        (os.urandom(32), os.urandom(120)),
        (os.urandom(64), os.urandom(300)),
    ]
    for key, msg in cases:
        got = await hmac_run(dut, key, msg)
        ref = _hmac.new(key, msg, hashlib.sha512).digest()
        assert got == ref, f"key={key!r} len(msg)={len(msg)}: {got.hex()} != {ref.hex()}"
    dut._log.info(f"HMAC-SHA512 RTL verified bit-exact on {len(cases)} cases")
