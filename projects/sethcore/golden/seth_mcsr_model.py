"""SethCore machine-mode CSR file — golden reference model.

Specifies the RV32 M-mode CSR subset the seth_mcsr RTL implements, with exact
WARL (Write-Any Read-Legal) legalisation so the RTL can be checked bit-for-bit.
This is the CSR *storage + read/modify/write datapath* only; trap side-effects
(auto-writing mepc/mcause on an exception) belong to the core-integration step and
are NOT modelled here.

CSR operations (csrrw/csrrs/csrrc and their immediate forms) follow RISC-V Zicsr:
  - the value written to rd is the CSR's current (pre-write) read value;
  - csrrw writes `operand`; csrrs writes read|operand; csrrc writes read&~operand;
  - csrrs/csrrc with a zero operand (rs1=x0 or uimm=0) perform NO write (read-only);
  - the raw write value is then WARL-legalised per CSR before being stored.

Reads of read-only / unimplemented bits return their fixed legal value.
"""

MASK32 = 0xFFFFFFFF

# CSR addresses
MSTATUS, MISA, MIE, MTVEC = 0x300, 0x301, 0x304, 0x305
MSCRATCH, MEPC, MCAUSE, MTVAL, MIP = 0x340, 0x341, 0x342, 0x343, 0x344
MVENDORID, MARCHID, MIMPID, MHARTID = 0xF11, 0xF12, 0xF13, 0xF14

# misa: MXL=1 (32-bit, bits[31:30]=01) + extensions I (bit8) + M (bit12)
MISA_VAL = (1 << 30) | (1 << 8) | (1 << 12)          # 0x40001100
# mstatus writable bits: MIE(3), MPIE(7). MPP(12:11) is WARL-fixed to 2'b11 (M-only).
MSTATUS_WMASK = (1 << 3) | (1 << 7)
MSTATUS_MPP = 0b11 << 11
# mie writable bits: MSIE(3), MTIE(7), MEIE(11)
MIE_WMASK = (1 << 3) | (1 << 7) | (1 << 11)


class MCsr:
    def __init__(self):
        # only writable state is stored; read-only CSRs are computed on read
        self.mstatus = 0        # holds MIE/MPIE (MPP added on read)
        self.mtvec = 0          # BASE[31:2] | MODE(bit0); bit1 forced 0
        self.mie = 0
        self.mscratch = 0
        self.mepc = 0           # bit0 forced 0
        self.mcause = 0
        self.mtval = 0

    def read(self, addr):
        """Current legal value of CSR `addr` (0 for anything unimplemented)."""
        a = addr & 0xFFF
        if a == MSTATUS:  return (self.mstatus & MSTATUS_WMASK) | MSTATUS_MPP
        if a == MISA:     return MISA_VAL
        if a == MIE:      return self.mie & MIE_WMASK
        if a == MTVEC:    return self.mtvec & MASK32
        if a == MSCRATCH: return self.mscratch & MASK32
        if a == MEPC:     return self.mepc & 0xFFFFFFFE
        if a == MCAUSE:   return self.mcause & MASK32
        if a == MTVAL:    return self.mtval & MASK32
        if a == MIP:      return 0                       # no soft-writable IPs here
        if a in (MVENDORID, MARCHID, MIMPID, MHARTID):  return 0
        return 0

    def _legalise_store(self, addr, raw):
        """Apply WARL legalisation and store `raw` into the addressed CSR."""
        a = addr & 0xFFF
        raw &= MASK32
        if a == MSTATUS:  self.mstatus = raw & MSTATUS_WMASK
        elif a == MIE:    self.mie = raw & MIE_WMASK
        elif a == MTVEC:  self.mtvec = (raw & 0xFFFFFFFC) | (raw & 0x1)   # bit1 forced 0
        elif a == MSCRATCH: self.mscratch = raw
        elif a == MEPC:   self.mepc = raw & 0xFFFFFFFE
        elif a == MCAUSE: self.mcause = raw
        elif a == MTVAL:  self.mtval = raw
        # everything else (misa, ids, mip) is read-only: writes ignored

    def step(self, valid, funct3, addr, rs1, zimm):
        """Execute one CSR instruction. Returns rd_val (the pre-write CSR value).
        `valid` gates the state update; funct3[1:0] selects RW/RS/RC, funct3[2]
        selects the immediate form (operand = zero-extended zimm)."""
        old = self.read(addr)
        if not valid:
            return old
        operand = (zimm & 0x1F) if (funct3 & 0b100) else (rs1 & MASK32)
        op = funct3 & 0b11
        do_write = False
        raw = old
        if op == 0b01:            # csrrw / csrrwi
            raw, do_write = operand, True
        elif op == 0b10:          # csrrs / csrrsi
            raw = old | operand
            do_write = operand != 0
        elif op == 0b11:          # csrrc / csrrci
            raw = old & (~operand & MASK32)
            do_write = operand != 0
        if do_write:
            self._legalise_store(addr, raw)
        return old
