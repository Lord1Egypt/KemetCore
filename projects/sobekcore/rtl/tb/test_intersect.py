"""cocotb testbench for SobekCore sobek_intersect."""
import os
import random
import struct
import sys
import math

import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import sobek_fp32 as fp32

def fbits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]

def frombits(u):
    return struct.unpack("<f", struct.pack("<I", u))[0]

async def drive_input(dut, o, d, v0, v1, v2):
    dut.valid_in.value = 1
    dut.o0.value, dut.o1.value, dut.o2.value = [fbits(x) for x in o]
    dut.d0.value, dut.d1.value, dut.d2.value = [fbits(x) for x in d]
    dut.v0_0.value, dut.v0_1.value, dut.v0_2.value = [fbits(x) for x in v0]
    dut.v1_0.value, dut.v1_1.value, dut.v1_2.value = [fbits(x) for x in v1]
    dut.v2_0.value, dut.v2_1.value, dut.v2_2.value = [fbits(x) for x in v2]
    await RisingEdge(dut.clk)
    dut.valid_in.value = 0

def fp32_raytri(o, d, v0, v1, v2):
    # exact hardware fp32 sequence
    e1 = [fp32.f32(fp32.f32(v1[i]) - fp32.f32(v0[i])) for i in range(3)]
    e2 = [fp32.f32(fp32.f32(v2[i]) - fp32.f32(v0[i])) for i in range(3)]
    tvec = [fp32.f32(fp32.f32(o[i]) - fp32.f32(v0[i])) for i in range(3)]
    pvec = fp32.cross(d, e2)
    det = fp32.dot3(e1, pvec)
    inv_det = fp32.recip(det)
    dot_u = fp32.dot3(tvec, pvec)
    u = fp32.f32(dot_u * inv_det)
    qvec = fp32.cross(tvec, e1)
    dot_v = fp32.dot3(d, qvec)
    v = fp32.f32(dot_v * inv_det)
    uv = fp32.f32(u + v)
    dot_t = fp32.dot3(e2, qvec)
    t = fp32.f32(dot_t * inv_det)
    w = fp32.f32(fp32.f32(1.0) - uv)
    
    # Range tests in HW
    EPS = frombits(0x33d6bf95)
    det_lt_eps = (not math.isnan(det)) and (fp32.f32(abs(det)) < EPS)
    u_lt_0 = (not math.isnan(u)) and (u < fp32.f32(0.0))
    u_gt_1 = (not math.isnan(u)) and (u > fp32.f32(1.0))
    v_lt_0 = (not math.isnan(v)) and (v < fp32.f32(0.0))
    uv_gt_1 = (not math.isnan(uv)) and (uv > fp32.f32(1.0))
    t_lt_eps = (not math.isnan(t)) and (t < EPS)
    
    miss = det_lt_eps or u_lt_0 or u_gt_1 or v_lt_0 or uv_gt_1 or t_lt_eps
    
    if miss:
        return None
    return {"hit": 1, "t": t, "u": u, "v": v, "w": w}

@cocotb.test()
async def test_intersect(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.rst_n.value = 0
    dut.valid_in.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    V0 = [0.0, 0.0, 0.0]
    V1 = [1.0, 0.0, 0.0]
    V2 = [0.0, 1.0, 0.0]
    
    cases = [
        ([0.25, 0.25, 1.0], [0.0, 0.0, -1.0], V0, V1, V2), # hit center
        ([2.0, 2.0, 1.0], [0.0, 0.0, -1.0], V0, V1, V2), # miss
        ([0.25, 0.25, 1.0], [1.0, 0.0, 0.0], V0, V1, V2), # parallel
        ([0.25, 0.25, 1.0], [0.0, 0.0, 1.0], V0, V1, V2), # behind origin
    ]
    
    rng = random.Random(0x424242)
    for _ in range(500):
        # generate random triangles and rays
        v0 = [rng.uniform(-10, 10) for _ in range(3)]
        v1 = [rng.uniform(-10, 10) for _ in range(3)]
        v2 = [rng.uniform(-10, 10) for _ in range(3)]
        o = [rng.uniform(-10, 10) for _ in range(3)]
        d = [rng.uniform(-1, 1) for _ in range(3)]
        cases.append((o, d, v0, v1, v2))
    
    for o, d, v0, v1, v2 in cases:
        await drive_input(dut, o, d, v0, v1, v2)
        
        # wait 6 cycles for latency
        for _ in range(6):
            await RisingEdge(dut.clk)
            
        assert dut.valid_out.value == 1
        
        got_hit = int(dut.hit.value)
        exp = fp32_raytri(o, d, v0, v1, v2)
        
        if exp is None:
            assert got_hit == 0, f"Expected miss, got hit for {o} {d}"
        else:
            assert got_hit == 1, f"Expected hit, got miss for {o} {d}"
            got_t = frombits(int(dut.t.value))
            got_u = frombits(int(dut.u.value))
            got_v = frombits(int(dut.v.value))
            got_w = frombits(int(dut.w.value))
            # exact fp32 match
            assert fbits(got_t) == fbits(exp["t"])
            assert fbits(got_u) == fbits(exp["u"])
            assert fbits(got_v) == fbits(exp["v"])
            assert fbits(got_w) == fbits(exp["w"])
            
        await RisingEdge(dut.clk)
