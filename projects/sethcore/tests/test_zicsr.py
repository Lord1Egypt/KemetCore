"""Phase 0/1 tests for the RV32IMZicsr golden (CpuZ): CSR instruction execution
and M-mode trap / mret semantics, reusing the seth_mcsr / seth_trap models. Also
asserts the base Cpu still halts on 0x73 (no regression from the _system hook)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "golden"))
from seth_rv32im import Cpu                       # noqa: E402
from seth_rv32im_zicsr import CpuZ                # noqa: E402

MSTATUS, MTVEC, MEPC, MCAUSE, MSCRATCH = 0x300, 0x305, 0x341, 0x342, 0x340


def _addi(rd, rs1, imm):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13


def _csr(csr, rs1, f3, rd):
    return (csr << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x73


ECALL, EBREAK, MRET = 0x00000073, 0x00100073, 0x30200073


def test_base_cpu_still_halts_on_ecall():
    """Regression guard: the base RV32IM sim must keep halting on 0x73."""
    c = Cpu()
    c.load([ECALL])
    c.run()
    assert c.halted


def test_csr_read_modify_write():
    c = CpuZ()
    # x6=0x123; csrrw x5,mscratch,x6 (x5<-old=0, mscratch<-0x123);
    # csrrs x7,mscratch,x0 (x7<-0x123, no write); csrrci x8,mscratch,0 (x8<-0x123, no write)
    c.load([_addi(6, 0, 0x123),
            _csr(MSCRATCH, 6, 0b001, 5),
            _csr(MSCRATCH, 0, 0b010, 7),
            _csr(MSCRATCH, 0, 0b111, 8)])
    for _ in range(4):
        c.step()
    assert c.x[5] == 0
    assert c.x[7] == 0x123 and c.x[8] == 0x123
    assert c.csr.read(MSCRATCH) == 0x123


def test_csrrwi_immediate():
    c = CpuZ()
    # csrrwi x5, mscratch, 17  -> mscratch = 17 (zero-extended uimm), x5 = old
    c.load([_csr(MSCRATCH, 17, 0b101, 5)])
    c.pc = 0
    c.step()
    assert c.csr.read(MSCRATCH) == 17 and c.x[5] == 0


def test_ecall_traps_to_mtvec_and_mret_returns():
    c = CpuZ()
    c.csr.mstatus = (1 << 3)          # MIE = 1
    c.csr.mtvec = 0x40                # direct mode
    c.load([ECALL])
    c.load([MRET], base=0x40)
    c.pc = 0
    c.step()                          # take the trap
    assert c.pc == 0x40               # jumped to the handler (mtvec base)
    assert c.csr.read(MEPC) == 0      # mepc = interrupted pc
    assert c.csr.read(MCAUSE) == 11   # ecall-from-M
    ms = c.csr.read(MSTATUS)
    assert (ms >> 3) & 1 == 0 and (ms >> 7) & 1 == 1   # MIE<-0, MPIE<-old MIE(1)
    c.step()                          # mret
    assert c.pc == 0                  # returned to mepc
    ms = c.csr.read(MSTATUS)
    assert (ms >> 3) & 1 == 1 and (ms >> 7) & 1 == 1   # MIE<-MPIE, MPIE<-1


def test_vectored_interrupt_and_ebreak_cause():
    # ebreak cause is 3
    c = CpuZ()
    c.csr.mtvec = 0x80
    c.load([EBREAK]); c.pc = 0
    c.step()
    assert c.pc == 0x80 and c.csr.read(MCAUSE) == 3
