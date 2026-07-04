"""SethCore RV32IMZicsr golden — the base RV32IM ISA sim extended with M-mode CSR
instructions and traps, WITHOUT touching seth_rv32im.py (whose ecall->halt the
existing core tests depend on). CpuZ overrides only the SYSTEM (0x73) hook and
reuses the verified seth_mcsr_model.MCsr + seth_trap_model, so it matches the
seth_mcsr / seth_trap RTL blocks. This is the reference for the future integrated
CSR-capable core (seth_core_csr).
"""
from seth_rv32im import Cpu, u32
from seth_mcsr_model import MCsr, MSTATUS, MTVEC, MEPC, MSTATUS_WMASK
from seth_trap_model import trap_enter, trap_return

CAUSE_EBREAK = 3
CAUSE_ECALL_M = 11


class CpuZ(Cpu):
    def __init__(self):
        super().__init__()
        self.csr = MCsr()

    def _trap(self, cause, is_int, tval):
        tgt, mepc, mcause, ms = trap_enter(
            self.pc, cause, is_int, self.csr.read(MTVEC), self.csr.read(MSTATUS))
        self.csr.mepc = mepc & 0xFFFFFFFE
        self.csr.mcause = mcause
        self.csr.mstatus = ms & MSTATUS_WMASK      # store only MIE/MPIE (MPP fixed on read)
        self.csr.mtval = tval
        return u32(tgt)

    def _mret(self):
        ret, ms = trap_return(self.csr.read(MEPC), self.csr.read(MSTATUS))
        self.csr.mstatus = ms & MSTATUS_WMASK
        return u32(ret)

    def _system(self, ins, f3, rd, rs1, npc):
        funct12 = (ins >> 20) & 0xFFF
        if f3 == 0:
            if funct12 == 0x000:      # ecall (M-mode)
                return self._trap(CAUSE_ECALL_M, 0, 0)
            if funct12 == 0x001:      # ebreak
                return self._trap(CAUSE_EBREAK, 0, self.pc)
            if funct12 == 0x302:      # mret
                return self._mret()
            return npc                # wfi / fence.i / other -> nop
        # CSR read/modify/write (csrrw/csrrs/csrrc + immediate forms)
        old = self.csr.read(funct12)
        self.csr.step(1, f3, funct12, self.x[rs1], rs1)   # rs1 field doubles as zimm
        self._wr(rd, old)
        return npc
