"""cocotb testbench for SethCore seth_core_csr — single-cycle RV32IMZicsr core,
bit-exact vs golden seth_rv32im_zicsr.CpuZ (regfile + M-mode CSRs) after running a
fixed number of cycles. Programs end in a self-loop (jal x0,0) since 0x73 no longer
halts (it is CSR/trap/mret)."""
import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
from seth_rv32im_zicsr import CpuZ  # noqa: E402


# ---- tiny RV32 encoders ---------------------------------------------------- #
def addi(rd, rs1, imm): return ((imm & 0xFFF) << 20) | (rs1 << 15) | (rd << 7) | 0x13
def csr(c, rs1, f3, rd): return (c << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x73
def jal(rd, off):
    o = off & 0x1FFFFF
    return (((o >> 20) & 1) << 31) | (((o >> 1) & 0x3FF) << 21) | (((o >> 11) & 1) << 20) \
        | (((o >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F
NOP = addi(0, 0, 0)
ECALL, MRET = 0x00000073, 0x30200073
CSRRW, CSRRS, CSRRWI = 0b001, 0b010, 0b101
MSTATUS, MTVEC, MEPC, MCAUSE, MSCRATCH = 0x300, 0x305, 0x341, 0x342, 0x340

CSR_REGS = {  # RTL stored-signal name -> MCsr attribute
    "mstatus_s": "mstatus", "mtvec_s": "mtvec", "mie_s": "mie", "mscratch_s": "mscratch",
    "mepc_s": "mepc", "mcause_s": "mcause", "mtval_s": "mtval",
}


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
    dut.rst.value = 0                      # deassert BEFORE loading (load path is under !rst)
    dut.load_en.value = 1
    for i, w in enumerate(words):
        dut.load_addr.value = 4 * i
        dut.load_data.value = w & 0xFFFFFFFF
        await RisingEdge(dut.clk)
    dut.load_en.value = 0


async def run_and_check(dut, words, cycles, tag, irq=(0, 0, 0)):
    await load_program(dut, words)
    dut.irq_soft.value, dut.irq_timer.value, dut.irq_ext.value = irq
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    # golden (same interrupt lines held constant)
    ref = CpuZ()
    ref.load(words)
    ref.irq_soft, ref.irq_timer, ref.irq_ext = irq
    for _ in range(cycles):
        ref.step()
    # compare regfile
    for i in range(1, 32):
        got = int(dut.u_rf.regs[i].value)
        assert got == ref.x[i], f"{tag}: x{i} = {got:08x} != {ref.x[i]:08x}"
    # compare CSR stored state
    for sig, attr in CSR_REGS.items():
        got = int(getattr(dut, sig).value)
        exp = getattr(ref.csr, attr) & 0xFFFFFFFF
        assert got == exp, f"{tag}: CSR {sig} = {got:08x} != {exp:08x}"
    dut._log.info(f"seth_core_csr [{tag}] matches CpuZ (regs + CSRs)")


@cocotb.test()
async def test_csr_rmw(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    prog = [
        addi(6, 0, 0x123),
        csr(MSCRATCH, 6, CSRRW, 5),     # mscratch=0x123, x5=0
        csr(MSCRATCH, 0, CSRRS, 7),     # x7=0x123
        csr(MTVEC, 3, CSRRWI, 8),       # mtvec = uimm 3 -> WARL -> bit1 forced 0 -> 0x1; x8=old
        jal(0, 0),                      # self-loop
    ]
    await run_and_check(dut, prog, 20, "csr_rmw")


@cocotb.test()
async def test_trap_roundtrip(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    prog = [
        addi(5, 0, 0x20),               # 0x00 x5 = handler addr 0x20
        csr(MTVEC, 5, CSRRW, 0),        # 0x04 mtvec = 0x20 (direct)
        csr(MSTATUS, 8, CSRRWI, 0),     # 0x08 mstatus = 8 -> MIE=1
        addi(10, 0, 1),                 # 0x0C x10 = 1
        ECALL,                          # 0x10 trap -> mtvec, mepc=0x10, mcause=11
        addi(11, 0, 2),                 # 0x14 x11 = 2 (after mret)
        jal(0, 0),                      # 0x18 self-loop
        NOP,                            # 0x1C
        addi(12, 0, 3),                 # 0x20 handler: x12 = 3
        csr(MEPC, 0, CSRRS, 13),        # 0x24 x13 = mepc (0x10)
        addi(13, 13, 4),                # 0x28 x13 = 0x14 (skip the ecall)
        csr(MEPC, 13, CSRRW, 0),        # 0x2C mepc = 0x14
        MRET,                           # 0x30 return to 0x14
    ]
    await run_and_check(dut, prog, 40, "trap_roundtrip")
    # spot-checks on the golden-confirmed architectural effects
    assert int(dut.u_rf.regs[10].value) == 1
    assert int(dut.u_rf.regs[11].value) == 2
    assert int(dut.u_rf.regs[12].value) == 3
    assert int(dut.mcause_s.value) == 11

@cocotb.test()
async def test_illegal_instruction_trap(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    ILLEGAL = 0x0000000B                 # custom-0 opcode 0x0B -> illegal in RV32IM+Zicsr
    prog = [
        addi(5, 0, 0x14),                # 0x00 x5 = handler @ 0x14 (word 5)
        csr(MTVEC, 5, CSRRW, 0),         # 0x04 mtvec = 0x14
        addi(9, 0, 7),                   # 0x08 x9 = 7 (marker)
        ILLEGAL,                         # 0x0C illegal -> trap (mcause=2, mtval=ins, mepc=0x0C)
        addi(10, 0, 9),                  # 0x10 (skipped; handler doesn't return here)
        jal(0, 0),                       # 0x14 handler: self-loop
    ]
    await run_and_check(dut, prog, 15, "illegal")
    assert int(dut.mcause_s.value) == 2, f"mcause={int(dut.mcause_s.value)}"
    assert int(dut.mtval_s.value) == ILLEGAL, f"mtval={int(dut.mtval_s.value):08x}"
    assert int(dut.mepc_s.value) == 0x0C
    assert int(dut.u_rf.regs[10].value) == 0     # instruction after illegal never ran

@cocotb.test()
async def test_timer_interrupt(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    MIE = 0x304
    prog = [
        addi(5, 0, 0x40),               # 0x00 mtvec base 0x40 (direct)
        csr(MTVEC, 5, CSRRW, 0),        # 0x04 mtvec = 0x40
        addi(6, 0, 0x80),               # 0x08 x6 = MTIE (bit7)
        csr(MIE, 6, CSRRW, 0),          # 0x0C mie = 0x80
        csr(MSTATUS, 8, CSRRWI, 0),     # 0x10 mstatus.MIE = 1  -> ints enabled
        addi(9, 0, 1),                  # 0x14 main marker (runs after the ISR returns)
        jal(0, 0),                      # 0x18 self-loop
    ] + [NOP] * 9 + [                   # pad to word 16 (0x40)
        addi(10, 0, 2),                 # 0x40 ISR: marker
        csr(MIE, 0, CSRRW, 0),          # 0x44 mie = 0 (stop re-firing)
        MRET,                           # 0x48 return to mepc (0x14)
    ]
    # timer irq held high throughout; the interrupt fires right after 0x10 enables MIE
    await run_and_check(dut, prog, 30, "timer_int", irq=(0, 1, 0))
    assert int(dut.u_rf.regs[9].value) == 1     # main instruction eventually ran
    assert int(dut.u_rf.regs[10].value) == 2    # ISR ran
    assert int(dut.mcause_s.value) == ((1 << 31) | 7)   # interrupt | timer cause

@cocotb.test()
async def test_wfi(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    MIE = 0x304
    WFI = 0x10500073
    prog = [
        addi(6, 0, 0x80),               # 0x00 x6 = MTIE
        csr(MIE, 6, CSRRW, 0),          # 0x04 mie = MTIE (mstatus.MIE stays 0 -> no trap)
        WFI,                            # 0x08 wait for interrupt
        addi(9, 0, 3),                  # 0x0C runs only once wfi wakes
        jal(0, 0),                      # 0x10 self-loop
    ]
    # no interrupt pending -> wfi stalls forever, x9 never written (matches CpuZ)
    await run_and_check(dut, prog, 20, "wfi_stall", irq=(0, 0, 0))
    assert int(dut.u_rf.regs[9].value) == 0
    # timer pending (MIE=0 so not taken as a trap, but wfi wakes) -> proceeds
    await run_and_check(dut, prog, 20, "wfi_wake", irq=(0, 1, 0))
    assert int(dut.u_rf.regs[9].value) == 3

