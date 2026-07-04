"""SethCore trap controller — golden reference model.

Computes the RISC-V M-mode trap vectoring and the CSR side-effects the seth_trap
RTL produces, so it can be checked bit-for-bit. Pairs with seth_mcsr (which stores
the resulting mepc/mcause/mstatus). mstatus bit layout matches seth_mcsr:
MIE=bit3, MPIE=bit7, MPP=bits[12:11] (fixed 2'b11, M-mode only).
"""

MASK32 = 0xFFFFFFFF


def trap_enter(pc, cause, is_interrupt, mtvec, mstatus):
    """On taking a trap: return (target, mepc_next, mcause_next, mstatus_next).
      target  = mtvec BASE, or BASE + 4*cause for an interrupt when mtvec.MODE=1
      mepc    = the interrupted pc (bit0 cleared)
      mcause  = (is_interrupt << 31) | cause
      mstatus : MPIE <- MIE, MIE <- 0, MPP <- 2'b11
    """
    base = mtvec & 0xFFFFFFFC
    vectored = (mtvec & 0x1) == 1
    is_int = is_interrupt & 1
    c = cause & 0x7FFFFFFF
    target = (base + 4 * c) & MASK32 if (is_int and vectored) else base
    mepc = pc & 0xFFFFFFFE
    mcause = ((is_int << 31) | c) & MASK32
    mie_old = (mstatus >> 3) & 1
    ms = mstatus & ~((1 << 3) | (1 << 7) | (0b11 << 11))
    ms |= (mie_old << 7) | (0b11 << 11)                  # MIE=0, MPIE=old MIE, MPP=11
    return target, mepc, mcause, ms & MASK32


def trap_return(mepc, mstatus):
    """On mret: return (ret_target, mstatus_next).
      ret_target = mepc (bit0 cleared)
      mstatus    : MIE <- MPIE, MPIE <- 1
    """
    ret = mepc & 0xFFFFFFFE
    mpie_old = (mstatus >> 7) & 1
    ms = mstatus & ~((1 << 3) | (1 << 7))
    ms |= (mpie_old << 3) | (1 << 7)                     # MIE=old MPIE, MPIE=1
    return ret, ms & MASK32
