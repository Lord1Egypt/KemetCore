"""cocotb testbench for SethCore seth_core_seq — MULTI-CYCLE RV32IMZicsr core
(iterative mul/div). Because the sequential unit takes many cycles per M-op, the
RTL retires instructions slower than CpuZ steps. Every test program ends in a
stable self-loop (jal x0,0), so we run BOTH to convergence (a generous budget)
and compare the settled architectural state — regfile + M-mode CSRs — to the
golden seth_rv32im_zicsr.CpuZ."""
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
from seth_rv32im_zicsr import CpuZ  # noqa: E402


# ---- tiny RV32 encoders ---------------------------------------------------- #
def addi(rd, rs1, imm): return ((imm & 0xFFF) << 20) | (rs1 << 15) | (rd << 7) | 0x13
def lui(rd, imm20):     return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | 0x37
def rtype(f7, rs2, rs1, f3, rd): return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x33
def mul(rd, rs1, rs2):  return rtype(0x01, rs2, rs1, 0x0, rd)
def mulh(rd, rs1, rs2): return rtype(0x01, rs2, rs1, 0x1, rd)
def div(rd, rs1, rs2):  return rtype(0x01, rs2, rs1, 0x4, rd)
def divu(rd, rs1, rs2): return rtype(0x01, rs2, rs1, 0x5, rd)
def rem(rd, rs1, rs2):  return rtype(0x01, rs2, rs1, 0x6, rd)
def remu(rd, rs1, rs2): return rtype(0x01, rs2, rs1, 0x7, rd)
def add(rd, rs1, rs2):  return rtype(0x00, rs2, rs1, 0x0, rd)
def sub(rd, rs1, rs2):  return rtype(0x20, rs2, rs1, 0x0, rd)
def jal(rd, off):
    o = off & 0x1FFFFF
    return (((o >> 20) & 1) << 31) | (((o >> 1) & 0x3FF) << 21) | (((o >> 11) & 1) << 20) \
        | (((o >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F
def csr(c, rs1, f3, rd): return (c << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x73
LOOP = jal(0, 0)   # self-loop terminator
CSRRW, CSRRS = 0b001, 0b010
MSCRATCH = 0x340

CSR_REGS = {
    "mstatus_s": "mstatus", "mtvec_s": "mtvec", "mie_s": "mie", "mscratch_s": "mscratch",
    "mepc_s": "mepc", "mcause_s": "mcause", "mtval_s": "mtval",
}


def li(rd, val):
    """load a 32-bit constant with lui+addi (addi sign-extends, so pre-bias)."""
    val &= 0xFFFFFFFF
    hi = (val + 0x800) >> 12
    lo = val - ((hi << 12) & 0xFFFFFFFF)
    lo = ((lo + 0x800) & 0xFFF) - 0x800   # sign-extended low 12
    return [lui(rd, hi & 0xFFFFF), addi(rd, rd, lo & 0xFFF)]


async def load_program(dut, words):
    dut.rst.value = 1
    dut.load_en.value = 0
    dut.load_addr.value = 0
    dut.load_data.value = 0
    dut.irq_soft.value = 0
    dut.irq_timer.value = 0
    dut.irq_ext.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    dut.load_en.value = 1
    for i, w in enumerate(words):
        dut.load_addr.value = 4 * i
        dut.load_data.value = w & 0xFFFFFFFF
        await RisingEdge(dut.clk)
    dut.load_en.value = 0


async def run_prog(dut, words, tag):
    await load_program(dut, words)
    budget = 60 * len(words) + 400          # generous: covers ~34-cycle divides
    for _ in range(budget):
        await RisingEdge(dut.clk)
    ref = CpuZ()
    ref.load(words)
    for _ in range(len(words) + 50):        # CpuZ retires 1 instr/step -> settles fast
        ref.step()
    for i in range(1, 32):
        got = int(dut.u_rf.regs[i].value)
        assert got == ref.x[i], f"{tag}: x{i} = {got:08x} != {ref.x[i]:08x}"
    for sig, attr in CSR_REGS.items():
        got = int(getattr(dut, sig).value)
        exp = getattr(ref.csr, attr) & 0xFFFFFFFF
        assert got == exp, f"{tag}: CSR {sig} = {got:08x} != {exp:08x}"
    dut._log.info(f"seth_core_seq [{tag}] converged == CpuZ")


@cocotb.test()
async def test_muldiv_program(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    # exercise every M op incl. negative, div-by-zero, INT_MIN/-1 overflow
    prog = []
    prog += li(1, 1000)
    prog += li(2, 7)
    prog += li(3, 0x80000000)     # INT_MIN
    prog += li(4, 0xFFFFFFFF)     # -1
    prog += li(5, 0)              # zero divisor
    prog += [
        mul(10, 1, 2),            # 7000
        div(11, 1, 2),            # 142
        rem(12, 1, 2),            # 6
        div(13, 3, 4),            # INT_MIN / -1 -> INT_MIN (overflow)
        rem(14, 3, 4),            # -> 0
        div(15, 1, 5),            # /0 -> -1
        rem(16, 1, 5),            # /0 -> dividend 1000
        divu(17, 3, 2),           # unsigned INT_MIN / 7
        remu(18, 3, 2),
        mulh(19, 3, 4),           # signed high product
        sub(20, 11, 12),
        add(21, 10, 11),
        LOOP,
    ]
    await run_prog(dut, prog, "muldiv")

    # ---- program 2: dependent chain + CSR RMW (same test => one clock) ------ #
    # each op consumes the previous result, proving the stall interlock feeds the
    # right operands and that non-M instructions still run between divides.
    prog = []
    prog += li(1, 123456)
    prog += li(2, 17)
    prog += [
        div(3, 1, 2),             # 7262
        rem(4, 1, 2),             # 2
        mul(5, 3, 2),             # 7262*17
        add(6, 5, 4),             # == 1's original... ~123456
        divu(7, 6, 3),
        csr(MSCRATCH, 6, CSRRW, 8),   # mscratch <- x6 ; x8 <- old(0)
        csr(MSCRATCH, 0, CSRRS, 9),   # x9 <- mscratch (== x6)
        LOOP,
    ]
    await run_prog(dut, prog, "chain+csr")
