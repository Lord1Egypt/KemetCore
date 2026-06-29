"""cocotb testbench for NeithCore neith_msgcodec — bit-exact vs golden _encode/_decode.

ENCODE: stream 256 message bits, read 256 coefficients, check == golden._encode(bits).
DECODE: stream 256 coefficients, read 256 bits, check == golden._decode(poly). Covers
the decode threshold boundaries (Q/4, 3Q/4) exactly, plus the encode(decode) round trip
and random vectors.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as golden  # noqa: E402

Q = golden.Q
N = golden.N  # 256


async def reset(dut):
    dut.start.value = 0
    dut.mode.value = 0
    dut.in_valid.value = 0
    dut.in_data.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run(dut, data, mode):
    dut.start.value = 1
    dut.mode.value = mode
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for j in range(N):
        dut.in_valid.value = 1
        dut.in_data.value = int(data[j]) & 0x1FFF
        await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    for _ in range(50):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "engine did not assert done in time"
    out = []
    for addr in range(N):
        dut.rd_addr.value = addr
        await Timer(1, units="ns")
        out.append(int(dut.out_data.value))
    return out


@cocotb.test()
async def test_msgcodec(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x33C0)

    # ENCODE: random bit messages -> coefficients
    for _ in range(6):
        bits = [rng.getrandbits(1) for _ in range(N)]
        got = await run(dut, bits, 0)
        assert got == golden._encode(bits)

    # DECODE: threshold boundaries (q4=1920, q34=5760 are EXCLUDED; +/-1 around them)
    q4, q34 = Q // 4, 3 * Q // 4
    bounds = [0, q4 - 1, q4, q4 + 1, q34 - 1, q34, q34 + 1, Q - 1,
              Q // 2, 1, 2, 3, 4, 5, 6, 7]
    poly = [bounds[i % len(bounds)] for i in range(N)]
    got = await run(dut, poly, 1)
    assert got == golden._decode(poly)

    # DECODE: random coefficients
    for _ in range(6):
        poly = [rng.randrange(Q) for _ in range(N)]
        got = await run(dut, poly, 1)
        assert got == golden._decode(poly)

    # round trip: decode(encode(bits)) == bits
    bits = [rng.getrandbits(1) for _ in range(N)]
    coeffs = await run(dut, bits, 0)
    back = await run(dut, coeffs, 1)
    assert back == bits

    dut._log.info("neith_msgcodec: encode/decode (boundaries + random + round trip) match golden")
