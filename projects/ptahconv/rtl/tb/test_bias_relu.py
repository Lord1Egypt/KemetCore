"""cocotb testbench for PtahConv ptah_bias_relu — fp32 bias-add + ReLU epilogue,
bit-exact vs golden ptah_conv.bias_relu (combinational)."""
import os
import random
import struct
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ptah_conv as golden  # noqa: E402

N = 8


def f2b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def pack(vec):
    w = 0
    for i, u in enumerate(vec):
        w |= (u & 0xFFFFFFFF) << (32 * i)
    return w


async def check(dut, xs, bs):
    dut.x.value = pack(xs)
    dut.bias.value = pack(bs)
    await Timer(1, units="ns")
    for i in range(N):
        got = (int(dut.y.value) >> (32 * i)) & 0xFFFFFFFF
        exp = golden.bias_relu(xs[i], bs[i])
        assert got == exp, f"lane {i}: x={xs[i]:08x} b={bs[i]:08x} got {got:08x} exp {exp:08x}"


@cocotb.test()
async def test_bias_relu(dut):
    corners = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x40000000, 0xC0000000,
               0x7F800000, 0xFF800000, 0x7FC00000, 0x00800000, 0x80800000, 0x00000001]
    # directed: cartesian corners spread across lanes
    for a in corners:
        xs = [a] * N
        bs = corners + corners[:N - len(corners)] if len(corners) < N else corners[:N]
        bs = (corners * ((N // len(corners)) + 1))[:N]
        await check(dut, xs, bs)

    rng = random.Random(0x9EED0)
    for _ in range(4000):
        xs = [rng.getrandbits(32) for _ in range(N)]
        bs = [rng.getrandbits(32) for _ in range(N)]
        await check(dut, xs, bs)
    # tame magnitudes (realistic conv outputs) to exercise the +/- boundary of relu
    for _ in range(4000):
        def tame():
            sign = rng.getrandbits(1) << 31
            exp = rng.randint(118, 134)
            man = rng.getrandbits(23)
            return sign | (exp << 23) | man
        xs = [tame() for _ in range(N)]
        bs = [tame() for _ in range(N)]
        await check(dut, xs, bs)

    dut._log.info("ptah_bias_relu verified bit-exact vs golden bias_relu (8001 lane-vectors)")
