"""cocotb testbench for atum_vcore — the AtumCore single-cycle vector core.

Preload the instruction memory + initial vector registers, run to HALT, and compare
the whole vector register file against a golden runner that executes the same
micro-program on the golden VectorUnit. Random programs use integer ops + reductions
(exact compare); fp ops are exercised in the directed program with chosen values.
"""
import os
import random
import struct
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import atum_rvv as g  # noqa: E402

NREGS = 32
VLMAX = 8
ELEN = 32
VLEN = VLMAX * ELEN
MASKW = (1 << ELEN) - 1

ALU_NAMES = {0: "vadd", 1: "vsub", 2: "vmul", 3: "vand", 4: "vor",
             5: "vxor", 6: "vsll", 7: "vsrl", 8: "vmacc"}

K_VSETVL, K_VOP, K_VHALT = 0, 1, 2


def enc(kind, vd=0, vs1=0, vs2=0, vclass=0, subop=0, avl=0):
    return ((kind & 3) | ((vd & 31) << 2) | ((vs1 & 31) << 7) | ((vs2 & 31) << 12)
            | ((vclass & 3) << 17) | ((subop & 15) << 19) | ((avl & 0x1FF) << 23))


def VSETVL(avl):                    return enc(K_VSETVL, avl=avl)
def VOP(vclass, subop, vd, vs1, vs2): return enc(K_VOP, vd, vs1, vs2, vclass, subop)
def HALT():                          return enc(K_VHALT)


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def f32b(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def run_golden(initial, prog):
    vu = g.VectorUnit()
    for r, lanes in initial.items():
        vu.vreg[r] = np.array(lanes, dtype=np.uint32)
    for w in prog:
        kind = w & 3
        if kind == K_VHALT:
            break
        if kind == K_VSETVL:
            vu.vsetvl((w >> 23) & 0x1FF)
        elif kind == K_VOP:
            vd = (w >> 2) & 31; vs1 = (w >> 7) & 31; vs2 = (w >> 12) & 31
            vclass = (w >> 17) & 3; subop = (w >> 19) & 15
            if vclass == 0:
                getattr(vu, ALU_NAMES[subop])(vd, vs1, vs2)
            elif vclass == 1:
                (vu.vfmul if (subop & 1) else vu.vfadd)(vd, vs1, vs2)
            else:
                scalar = int(vu.vredmax(vs1) if (subop & 1) else vu.vredsum(vs1)) & MASKW
                out = vu.vreg[vd].copy()
                out[0] = scalar
                vu.vreg[vd] = out
    return [[int(x) for x in vu.vreg[r].astype(np.uint32)] for r in range(NREGS)]


async def load_and_run(dut, prog, initial, max_cycles=4000):
    dut.rst.value = 1
    dut.load_imem.value = 0
    dut.load_vreg.value = 0
    dut.load_iaddr.value = 0
    dut.load_idata.value = 0
    dut.load_vaddr.value = 0
    dut.load_vdata.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    # preload vector registers
    dut.load_vreg.value = 1
    for r, lanes in initial.items():
        dut.load_vaddr.value = r
        dut.load_vdata.value = pack(lanes)
        await RisingEdge(dut.clk)
    dut.load_vreg.value = 0
    # preload instruction memory
    dut.load_imem.value = 1
    for i, w in enumerate(prog):
        dut.load_iaddr.value = i
        dut.load_idata.value = int(w)
        await RisingEdge(dut.clk)
    dut.load_imem.value = 0
    # run
    cyc = 0
    while cyc < max_cycles:
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.halted.value) == 1:
            break
        cyc += 1
    assert cyc < max_cycles, "vcore did not halt"


def hw_regs(dut):
    return [[(int(dut.u_rf.regs[r].value) >> (i * ELEN)) & MASKW for i in range(VLMAX)]
            for r in range(NREGS)]


async def run(dut, prog, initial):
    await load_and_run(dut, prog, initial)
    exp = run_golden(initial, prog)
    got = hw_regs(dut)
    for r in range(NREGS):
        assert got[r] == exp[r], f"v{r}: hw {got[r]} != golden {exp[r]}"


@cocotb.test()
async def test_directed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    # integer axpy-ish + dot, fp mul/add, reduction, partial vl
    init = {
        1: [1, 2, 3, 4, 5, 6, 7, 8],
        2: [10, 20, 30, 40, 50, 60, 70, 80],
        3: [2] * 8,
        5: [f32b(1.5), f32b(2.0), f32b(-3.0), f32b(0.5), f32b(8.0), f32b(-1.0), f32b(100.0), f32b(0.25)],
        6: [f32b(2.0)] * 8,
    }
    prog = [
        VOP(0, 0, 10, 1, 2),     # v10 = v1 + v2
        VOP(0, 2, 11, 1, 3),     # v11 = v1 * 2  (vmul)
        VOP(0, 8, 2, 1, 3),      # v2 += v1*v3   (vmacc, in place)
        VOP(2, 0, 12, 1, 0),     # v12[0] = sum(v1)   (vredsum)
        VOP(2, 1, 13, 2, 0),     # v13[0] = max(v2)   (vredmax)
        VOP(1, 1, 14, 5, 6),     # v14 = v5 * v6 (vfmul)
        VOP(1, 0, 15, 5, 5),     # v15 = v5 + v5 (vfadd)
        VSETVL(4),               # vl = 4
        VOP(0, 0, 16, 1, 2),     # v16 = v1 + v2 only lanes 0..3 (rest 0 from reset)
        HALT(),
    ]
    await run(dut, prog, init)
    dut._log.info("atum_vcore: directed program (int/fp/reduction/vsetvl) matches golden")


@cocotb.test()
async def test_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0xA70C0DE)
    for _ in range(40):
        nregs_init = rng.randint(2, 8)
        init = {r: [rng.getrandbits(32) for _ in range(VLMAX)]
                for r in range(1, 1 + nregs_init)}
        prog = []
        if rng.random() < 0.5:
            prog.append(VSETVL(rng.randint(1, VLMAX)))
        for _ in range(rng.randint(6, 20)):
            if rng.random() < 0.25:
                # reduction over a populated source into a dest
                vs1 = rng.randint(1, nregs_init)
                prog.append(VOP(2, rng.randint(0, 1), rng.randint(9, 20), vs1, 0))
            else:
                op = rng.randint(0, 8)
                prog.append(VOP(0, op, rng.randint(9, 31),
                                rng.randint(1, nregs_init), rng.randint(1, nregs_init)))
            if rng.random() < 0.15:
                prog.append(VSETVL(rng.randint(1, VLMAX)))
        prog.append(HALT())
        await run(dut, prog, init)
    dut._log.info("atum_vcore: 40 random int/reduction programs match golden")
