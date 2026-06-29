"""cocotb testbench for PtahConv ptah_gemm — bit-exact vs golden matmul_seq."""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ptah_conv as golden  # noqa: E402


def f2b(x):
    return int(np.frombuffer(struct.pack("<f", np.float32(x)), np.uint32)[0])


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def reset(dut):
    dut.load_en.value = 0
    dut.load_sel.value = 0
    dut.load_addr.value = 0
    dut.load_data.value = 0
    dut.start.value = 0
    dut.M.value = 0
    dut.N.value = 0
    dut.K.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def preload(dut, sel, flat):
    dut.load_sel.value = sel
    for addr, val in enumerate(flat):
        dut.load_addr.value = addr
        dut.load_data.value = val
        dut.load_en.value = 1
        await RisingEdge(dut.clk)
    dut.load_en.value = 0


async def gemm(dut, A, B, M, N, K):
    await preload(dut, 0, [A[i][k] for i in range(M) for k in range(K)])
    await preload(dut, 1, [B[k][j] for k in range(K) for j in range(N)])
    dut.M.value = M
    dut.N.value = N
    dut.K.value = K
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for _ in range(M * N * (K + 4) + 50):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "gemm did not finish"
    out = [[0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            dut.rd_addr.value = i * N + j
            await Timer(1, units="ns")
            out[i][j] = int(dut.c_data.value)
    return out


@cocotb.test()
async def test_gemm(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x9E33)

    def rf(n):
        out = []
        for _ in range(n):
            sign = rng.getrandbits(1) << 31
            exp = rng.randint(118, 132)
            out.append(sign | (exp << 23) | rng.getrandbits(23))
        return out

    # directed: identity-ish and 1x1
    A = [[f2b(1.0), f2b(2.0)], [f2b(3.0), f2b(4.0)]]
    B = [[f2b(1.0), f2b(0.0)], [f2b(0.0), f2b(1.0)]]
    got = await gemm(dut, A, B, 2, 2, 2)
    exp = golden.matmul_seq(A, B, 2, 2, 2)
    assert got == exp, f"identity: {got} != {exp}"

    for trial in range(40):
        M = rng.randint(1, 6); N = rng.randint(1, 6); K = rng.randint(1, 10)
        A = [rf(K) for _ in range(M)]
        B = [rf(N) for _ in range(K)]
        got = await gemm(dut, A, B, M, N, K)
        exp = golden.matmul_seq(A, B, M, N, K)
        for i in range(M):
            for j in range(N):
                if is_nan32(exp[i][j]):
                    assert is_nan32(got[i][j]), f"t{trial} ({i},{j}) nan"
                else:
                    assert got[i][j] == exp[i][j], \
                        f"t{trial} M{M}N{N}K{K} ({i},{j}): {got[i][j]:08x}!={exp[i][j]:08x}"
    dut._log.info("ptah_gemm verified bit-exact vs golden matmul_seq")
