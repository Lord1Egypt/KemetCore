"""cocotb testbench for ImentetCore imentet_core.sv — full attention datapath."""
import os
import sys
import struct
import numpy as np

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import imentet_attention  # noqa: E402


def float_to_int32(f):
    return struct.unpack('<I', struct.pack('<f', float(f)))[0]

def int32_to_float(i):
    return struct.unpack('<f', struct.pack('<I', i & 0xFFFFFFFF))[0]


@cocotb.test()
async def test_attention_pipeline(dut):
    """Test full attention datapath vs golden reference."""
    D = int(dut.D.value)
    LS = int(dut.LS.value)
    DV = int(dut.DV.value)

    np.random.seed(42)
    # Generate random test cases
    for i in range(10):
        # inputs
        Q = np.random.uniform(-2.0, 2.0, size=(D,)).astype(np.float32)
        K = np.random.uniform(-2.0, 2.0, size=(LS, D)).astype(np.float32)
        V = np.random.uniform(-2.0, 2.0, size=(LS, DV)).astype(np.float32)
        scale = np.float32(1.0 / np.sqrt(D))
        
        # causal mask (0 or -inf)
        # To make it causal, simulate this is row `row_idx` of a larger matrix.
        row_idx = np.random.randint(0, LS)
        mask = np.zeros((LS,), dtype=np.float32)
        for j in range(LS):
            if j > row_idx:
                mask[j] = -np.inf

        # drive Q
        q_int = 0
        for j in range(D):
            q_int |= (float_to_int32(Q[j]) << (32 * j))
        dut.q.value = q_int

        # drive K
        k_int = 0
        for j in range(LS):
            for d in range(D):
                k_int |= (float_to_int32(K[j, d]) << (32 * (j * D + d)))
        dut.k.value = k_int

        # drive V
        v_int = 0
        for j in range(LS):
            for d in range(DV):
                v_int |= (float_to_int32(V[j, d]) << (32 * (j * DV + d)))
        dut.v.value = v_int

        # drive scale and mask
        dut.s.value = float_to_int32(scale)
        
        m_int = 0
        for j in range(LS):
            m_int |= (float_to_int32(mask[j]) << (32 * j))
        dut.m.value = m_int

        await Timer(10, units='ns')

        # extract output
        out_int = int(dut.ctx.value)
        out_hw = np.zeros((DV,), dtype=np.float32)
        for d in range(DV):
            val = (out_int >> (32 * d)) & 0xFFFFFFFF
            out_hw[d] = int32_to_float(val)

        # golden (we pass Q as (1,D) to attention(), which expects (Lq, D))
        Q_2d = Q.reshape(1, D)
        mask_2d = mask.reshape(1, LS)
        golden_out_2d = imentet_attention.attention(Q_2d, K, V, mask_2d)
        golden_out = golden_out_2d[0].astype(np.float32)

        # check
        np.testing.assert_allclose(out_hw, golden_out, rtol=1e-5, atol=1e-5)
