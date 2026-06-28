"""cocotb testbench for atum_vcore — the AtumCore single-cycle vector core with memory.

Preload the instruction memory, the data memory and the initial vector registers,
run to HALT, then compare the whole machine state (vector register file + data
memory) against a golden runner that executes the same micro-program on the golden
VectorUnit. Includes a strip-mined integer axpy over memory; random programs use
integer ops / reductions / loads / stores (exact compare).
"""
import os
import random
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
DWORDS = 256
MASKW = (1 << ELEN) - 1

ALU_NAMES = {0: "vadd", 1: "vsub", 2: "vmul", 3: "vand", 4: "vor",
             5: "vxor", 6: "vsll", 7: "vsrl", 8: "vmacc"}

K_VSETVL, K_VOP, K_VHALT, K_VLD, K_VST = 0, 1, 2, 3, 4


def enc(kind, vd=0, vs1=0, vs2=0, vclass=0, subop=0, imm8=0):
    return ((kind & 7) | ((vd & 31) << 3) | ((vs1 & 31) << 8) | ((vs2 & 31) << 13)
            | ((vclass & 3) << 18) | ((subop & 15) << 20) | ((imm8 & 0xFF) << 24))


def VSETVL(avl):                       return enc(K_VSETVL, imm8=avl)
def VOP(vclass, subop, vd, vs1, vs2):  return enc(K_VOP, vd, vs1, vs2, vclass, subop)
def HALT():                            return enc(K_VHALT)
def VLD(vd, base):                     return enc(K_VLD, vd=vd, imm8=base)
def VST(vs1, base):                    return enc(K_VST, vs1=vs1, imm8=base)


def pack(lanes):
    v = 0
    for i, x in enumerate(lanes):
        v |= (int(x) & MASKW) << (i * ELEN)
    return v


def run_golden(init_vregs, init_dmem, prog):
    vu = g.VectorUnit()
    for r, lanes in init_vregs.items():
        vu.vreg[r] = np.array(lanes, dtype=np.uint32)
    dmem = list(init_dmem)
    for w in prog:
        kind = w & 7
        if kind == K_VHALT:
            break
        vd = (w >> 3) & 31; vs1 = (w >> 8) & 31; vs2 = (w >> 13) & 31
        vclass = (w >> 18) & 3; subop = (w >> 20) & 15; imm8 = (w >> 24) & 0xFF
        if kind == K_VSETVL:
            vu.vsetvl(imm8)
        elif kind == K_VOP:
            if vclass == 0:
                getattr(vu, ALU_NAMES[subop])(vd, vs1, vs2)
            elif vclass == 1:
                (vu.vfmul if (subop & 1) else vu.vfadd)(vd, vs1, vs2)
            else:
                scalar = int(vu.vredmax(vs1) if (subop & 1) else vu.vredsum(vs1)) & MASKW
                out = vu.vreg[vd].copy(); out[0] = scalar; vu.vreg[vd] = out
        elif kind == K_VLD:
            out = np.zeros(VLMAX, dtype=np.uint32)
            for i in range(vu.vl):
                out[i] = dmem[(imm8 + i) % DWORDS]
            vu.vreg[vd] = out
        elif kind == K_VST:
            for i in range(vu.vl):
                dmem[(imm8 + i) % DWORDS] = int(vu.vreg[vs1][i]) & MASKW
    return ([[int(x) for x in vu.vreg[r].astype(np.uint32)] for r in range(NREGS)], dmem)


async def load_and_run(dut, prog, init_vregs, init_dmem, max_cycles=6000):
    dut.rst.value = 1
    for s in ("load_imem", "load_dmem", "load_vreg"):
        getattr(dut, s).value = 0
    for s in ("load_iaddr", "load_idata", "load_daddr", "load_ddata", "load_vaddr", "load_vdata"):
        getattr(dut, s).value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    # preload data memory
    dut.load_dmem.value = 1
    for a, d in enumerate(init_dmem):
        dut.load_daddr.value = a
        dut.load_ddata.value = int(d) & MASKW
        await RisingEdge(dut.clk)
    dut.load_dmem.value = 0
    # preload vector registers
    dut.load_vreg.value = 1
    for r, lanes in init_vregs.items():
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


def hw_dmem(dut, n):
    return [int(dut.dmem[a].value) & MASKW for a in range(n)]


async def run(dut, prog, init_vregs, init_dmem):
    await load_and_run(dut, prog, init_vregs, init_dmem)
    exp_regs, exp_dmem = run_golden(init_vregs, init_dmem, prog)
    got_regs = hw_regs(dut)
    for r in range(NREGS):
        assert got_regs[r] == exp_regs[r], f"v{r}: hw {got_regs[r]} != golden {exp_regs[r]}"
    got_dmem = hw_dmem(dut, len(init_dmem))
    assert got_dmem == exp_dmem, "data memory mismatch"


@cocotb.test()
async def test_stripmined_axpy(dut):
    """Integer y[i] += a*x[i] over a length-20 array, strip-mined in VLMAX chunks
    via vsetvl + VLD/VMACC/VST — the real length-agnostic RVV idiom."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    n = 20
    a = 5
    rng = random.Random(0xA791)
    x = [rng.randint(0, 1000) for _ in range(n)]
    y = [rng.randint(0, 1000) for _ in range(n)]
    XB, YB = 0, 64
    dmem = [0] * DWORDS
    for i in range(n):
        dmem[XB + i] = x[i]
        dmem[YB + i] = y[i]
    init_vregs = {3: [a] * VLMAX}            # broadcast scalar a in v3
    prog = []
    off = 0
    while off < n:
        prog += [
            VSETVL(n - off),
            VLD(1, XB + off),                # v1 = x chunk
            VLD(2, YB + off),                # v2 = y chunk
            VOP(0, 8, 2, 1, 3),              # v2 += v1 * v3  (vmacc)
            VST(2, YB + off),                # store y chunk
        ]
        off += VLMAX
    prog.append(HALT())
    await run(dut, prog, init_vregs, dmem)
    dut._log.info("atum_vcore: strip-mined integer axpy over memory matches golden")


@cocotb.test()
async def test_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rng = random.Random(0xD0E5)
    for _ in range(40):
        dmem = [rng.getrandbits(32) for _ in range(64)] + [0] * (DWORDS - 64)
        ninit = rng.randint(2, 6)
        init_vregs = {r: [rng.getrandbits(32) for _ in range(VLMAX)] for r in range(1, 1 + ninit)}
        prog = [VSETVL(rng.randint(1, VLMAX))]
        for _ in range(rng.randint(8, 22)):
            pick = rng.random()
            if pick < 0.2:
                prog.append(VLD(rng.randint(1, 12), rng.randint(0, 48)))
            elif pick < 0.4:
                prog.append(VST(rng.randint(1, 12), rng.randint(0, 48)))
            elif pick < 0.55:
                vs1 = rng.randint(1, ninit)
                prog.append(VOP(2, rng.randint(0, 1), rng.randint(9, 20), vs1, 0))
            elif pick < 0.7:
                prog.append(VSETVL(rng.randint(1, VLMAX)))
            else:
                prog.append(VOP(0, rng.randint(0, 8), rng.randint(9, 31),
                                rng.randint(1, 12), rng.randint(1, 12)))
        prog.append(HALT())
        await run(dut, prog, init_vregs, dmem)
    dut._log.info("atum_vcore: 40 random programs (ops + reductions + loads/stores) match golden")
