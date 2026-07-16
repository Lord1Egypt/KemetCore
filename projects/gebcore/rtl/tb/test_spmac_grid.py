"""cocotb testbench for GebCore geb_spmac_grid — bit-exact vs golden.sparse_matmul.

Drives the default 4x4 output-stationary sparse systolic array. For an (R,K)x(K,C)
matmul where K is a multiple of 4, the 2:4 compressed weights provide K/2 kept
weights per column. We stream the K/2 kept weights for column j (skewed by j).
To match this, the K/4 groups of 4 activations for row i are each held for 2
consecutive cycles (skewed by i). Zero-padding outside the K/2-long window is a no-op.
"""
import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import geb_sparse as golden  # noqa: E402

R = 4
C = 4


def f32_to_bits(f):
    return int(np.float32(f).view(np.uint32))


def bits_to_f32(b):
    return float(np.uint32(b).view(np.float32))


def is_nan32(u):
    return ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0


async def reset(dut):
    dut.en.value = 0
    dut.clear.value = 0
    dut.a_group_in.value = 0
    dut.val_in.value = 0
    dut.idx_in.value = 0
    dut.rd_row.value = 0
    dut.rd_col.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_sparse_matmul(dut, A, val, idx, K):
    """A: (R, K) fp32 array, val: (K/2, C) fp32 array, idx: (K/2, C) uint8 array.
    Returns (R, C) fp32 bits."""
    KH = K // 2
    dut.a_group_in.value = 0
    dut.val_in.value = 0
    dut.idx_in.value = 0
    dut.clear.value = 0
    dut.en.value = 0
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Pulse clear to zero the array internally before feeding data
    dut.clear.value = 1
    await RisingEdge(dut.clk)
    dut.clear.value = 0

    dut.en.value = 1
    for t in range(R + C + KH + 2):
        a_val = 0
        v_val = 0
        i_val = 0
        for i in range(R):
            k = t - i
            if 0 <= k < KH:
                g = k // 2
                grp0 = f32_to_bits(A[i, 4*g + 0])
                grp1 = f32_to_bits(A[i, 4*g + 1])
                grp2 = f32_to_bits(A[i, 4*g + 2])
                grp3 = f32_to_bits(A[i, 4*g + 3])
                group_bits = (grp3 << 96) | (grp2 << 64) | (grp1 << 32) | grp0
                a_val |= (group_bits << (128 * i))

        for j in range(C):
            k = t - j
            if 0 <= k < KH:
                v_val |= (f32_to_bits(val[k, j]) << (32 * j))
                i_val |= (int(idx[k, j]) << (2 * j))

        dut.a_group_in.value = a_val
        dut.val_in.value = v_val
        dut.idx_in.value = i_val
        await RisingEdge(dut.clk)

    dut.en.value = 0

    out = [[0] * C for _ in range(R)]
    for i in range(R):
        for j in range(C):
            dut.rd_row.value = i
            dut.rd_col.value = j
            await Timer(1, units="ns")
            out[i][j] = int(dut.out_acc.value)
    return out


def rand_f32(rng):
    if rng.random() < 0.10:
        return rng.choice([0.0, -0.0, 1.0, -1.0])
    return (rng.random() - 0.5) * (10 ** rng.randint(-3, 3))


async def check(dut, A, Wp, K, tag):
    val, idx = golden.compress_2of4(Wp)
    got = await run_sparse_matmul(dut, A, val, idx, K)
    
    with np.errstate(invalid="ignore", over="ignore"):
        exp = golden.sparse_matmul(A, val, idx)
        
    for i in range(R):
        for j in range(C):
            e = f32_to_bits(exp[i, j])
            g = got[i][j]
            if is_nan32(e):
                assert is_nan32(g), f"{tag} K={K} ({i},{j}): got {g:08x}, expected NaN"
            else:
                assert g == e, f"{tag} K={K} cell ({i},{j}): got {g:08x} != exp {e:08x}"


@cocotb.test()
async def test_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x9E37)
    
    for trial in range(40):
        K = rng.choice([4, 8, 12, 16, 24])
        A = np.array([[rand_f32(rng) for _ in range(K)] for _ in range(R)], dtype=np.float32)
        W = np.array([[rand_f32(rng) for _ in range(C)] for _ in range(K)], dtype=np.float32)
        Wp = golden.prune_2of4(W)
        await check(dut, A, Wp, K, f"rand{trial}")
        
    dut._log.info("geb_spmac_grid: 40 random 4x4 sparse matmuls verified bit-exact vs golden")
