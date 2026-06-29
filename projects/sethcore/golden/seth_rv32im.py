"""SethCore golden reference — RV32IM ISA simulator + tiny label assembler.

Implements an RV32I + M-extension subset: arithmetic/logic/shift (reg+imm),
load/store, branches, jal/jalr, lui/auipc, and mul/div/rem. ecall halts.
The assembler resolves labels so test programs read like assembly.
"""
MASK = 0xFFFFFFFF


def u32(x):
    return x & MASK


def s32(x):
    x &= MASK
    return x - (1 << 32) if x & 0x80000000 else x


# --------------------------------------------------------------------------- #
# Encoders
# --------------------------------------------------------------------------- #
def _R(f7, rs2, rs1, f3, rd, op):
    return u32((f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op)


def _I(imm, rs1, f3, rd, op):
    return u32(((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op)


def _S(imm, rs2, rs1, f3, op):
    imm &= 0xFFF
    return u32(((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) |
               ((imm & 0x1F) << 7) | op)


def _B(imm, rs2, rs1, f3, op):
    imm &= 0x1FFF
    b12 = (imm >> 12) & 1
    b11 = (imm >> 11) & 1
    b10_5 = (imm >> 5) & 0x3F
    b4_1 = (imm >> 1) & 0xF
    return u32((b12 << 31) | (b10_5 << 25) | (rs2 << 20) | (rs1 << 15) |
               (f3 << 12) | (b4_1 << 8) | (b11 << 7) | op)


def _U(imm, rd, op):
    return u32((imm & 0xFFFFF000) | (rd << 7) | op)


def _J(imm, rd, op):
    imm &= 0x1FFFFF
    b20 = (imm >> 20) & 1
    b10_1 = (imm >> 1) & 0x3FF
    b11 = (imm >> 11) & 1
    b19_12 = (imm >> 12) & 0xFF
    return u32((b20 << 31) | (b10_1 << 21) | (b11 << 20) | (b19_12 << 12) |
               (rd << 7) | op)


# mnemonic -> encoder taking (addr, labels, *args)
def _rt(f7, f3):
    return lambda a, L, rd, rs1, rs2: _R(f7, rs2, rs1, f3, rd, 0x33)


def _it(f3, op=0x13):
    return lambda a, L, rd, rs1, imm: _I(imm, rs1, f3, rd, op)


def _sh(f7, f3):  # shift-immediate
    return lambda a, L, rd, rs1, sh: _R(f7, sh, rs1, f3, rd, 0x13)


def _ld(f3):
    return lambda a, L, rd, imm, rs1: _I(imm, rs1, f3, rd, 0x03)


def _st(f3):
    return lambda a, L, rs2, imm, rs1: _S(imm, rs2, rs1, f3, 0x23)


def _br(f3):
    return lambda a, L, rs1, rs2, label: _B(L[label] - a, rs2, rs1, f3, 0x63)


ENC = {
    "addi": _it(0x0), "slti": _it(0x2), "sltiu": _it(0x3), "xori": _it(0x4),
    "ori": _it(0x6), "andi": _it(0x7),
    "slli": _sh(0x00, 0x1), "srli": _sh(0x00, 0x5), "srai": _sh(0x20, 0x5),
    "add": _rt(0x00, 0x0), "sub": _rt(0x20, 0x0), "sll": _rt(0x00, 0x1),
    "slt": _rt(0x00, 0x2), "sltu": _rt(0x00, 0x3), "xor": _rt(0x00, 0x4),
    "srl": _rt(0x00, 0x5), "sra": _rt(0x20, 0x5), "or": _rt(0x00, 0x6),
    "and": _rt(0x00, 0x7),
    "mul": _rt(0x01, 0x0), "mulh": _rt(0x01, 0x1), "mulhsu": _rt(0x01, 0x2),
    "mulhu": _rt(0x01, 0x3), "div": _rt(0x01, 0x4), "divu": _rt(0x01, 0x5),
    "rem": _rt(0x01, 0x6), "remu": _rt(0x01, 0x7),
    "lw": _ld(0x2), "lh": _ld(0x1), "lb": _ld(0x0), "lhu": _ld(0x5), "lbu": _ld(0x4),
    "sw": _st(0x2), "sh": _st(0x1), "sb": _st(0x0),
    "lui": lambda a, L, rd, imm: _U(imm, rd, 0x37),
    "auipc": lambda a, L, rd, imm: _U(imm, rd, 0x17),
    "jal": lambda a, L, rd, label: _J(L[label] - a, rd, 0x6F),
    "jalr": lambda a, L, rd, rs1, imm: _I(imm, rs1, 0x0, rd, 0x67),
    "beq": _br(0x0), "bne": _br(0x1), "blt": _br(0x4), "bge": _br(0x5),
    "bltu": _br(0x6), "bgeu": _br(0x7),
    "ecall": lambda a, L: _I(0, 0, 0, 0, 0x73),
}


def assemble(prog):
    """prog: list of either 'label:' strings or (mnemonic, *args) tuples."""
    labels, addr, insns = {}, 0, []
    for item in prog:
        if isinstance(item, str):
            labels[item.rstrip(":")] = addr
        else:
            insns.append((addr, item))
            addr += 4
    return [ENC[mn](a, labels, *args) for a, (mn, *args) in insns]


# --------------------------------------------------------------------------- #
# CPU
# --------------------------------------------------------------------------- #
def _sext(v, bits):
    m = 1 << (bits - 1)
    return (v ^ m) - m


def decode_imm(ins):
    """RV32 immediate generator: the 32-bit immediate for `ins`, selected by its
    opcode/format and sign-extended where the ISA requires it. R-type and system
    instructions carry no immediate -> 0. Matches the extractions in Cpu.step."""
    op = ins & 0x7F
    if op in (0x13, 0x03, 0x67):                 # I-type (ALU-imm, load, jalr)
        return u32(_sext(ins >> 20, 12))
    if op == 0x23:                               # S-type (store)
        return u32(_sext((((ins >> 25) & 0x7F) << 5) | ((ins >> 7) & 0x1F), 12))
    if op == 0x63:                               # B-type (branch)
        return u32(_sext(((ins >> 31) << 12) | (((ins >> 7) & 1) << 11) |
                         (((ins >> 25) & 0x3F) << 5) | (((ins >> 8) & 0xF) << 1), 13))
    if op in (0x37, 0x17):                       # U-type (lui, auipc)
        return u32(ins & 0xFFFFF000)
    if op == 0x6F:                               # J-type (jal)
        return u32(_sext(((ins >> 31) << 20) | (((ins >> 12) & 0xFF) << 12) |
                         (((ins >> 20) & 1) << 11) | (((ins >> 21) & 0x3FF) << 1), 21))
    return 0


#: control signals produced by decode_ctrl / seth_decode (datapath control word)
CTRL_FIELDS = ("reg_write", "alu_src_imm", "a_src_pc", "mem_read", "mem_write",
               "branch", "jump", "jalr", "is_mdu", "wb_sel")
#: wb_sel: 0 = ALU/MDU compute, 1 = load data, 2 = PC+4 (link), 3 = immediate (LUI)


def decode_ctrl(ins):
    """Main control decoder: the datapath control word for `ins`, matching the
    behaviour of Cpu.step. Returns a dict over CTRL_FIELDS. Unknown / system
    opcodes produce an all-zero (no-op: no reg/mem write, no control transfer)
    word so an unimplemented instruction is inert."""
    op = ins & 0x7F
    f7 = (ins >> 25) & 0x7F
    c = dict.fromkeys(CTRL_FIELDS, 0)
    if op == 0x33:                               # R-type (+ M-extension)
        c["reg_write"] = 1
        c["is_mdu"] = 1 if f7 == 0x01 else 0
    elif op == 0x13:                             # I-type ALU
        c["reg_write"] = 1; c["alu_src_imm"] = 1
    elif op == 0x03:                             # load
        c["reg_write"] = 1; c["alu_src_imm"] = 1; c["mem_read"] = 1; c["wb_sel"] = 1
    elif op == 0x23:                             # store
        c["alu_src_imm"] = 1; c["mem_write"] = 1
    elif op == 0x63:                             # branch
        c["branch"] = 1
    elif op == 0x67:                             # jalr
        c["reg_write"] = 1; c["alu_src_imm"] = 1; c["jump"] = 1; c["jalr"] = 1; c["wb_sel"] = 2
    elif op == 0x6F:                             # jal
        c["reg_write"] = 1; c["jump"] = 1; c["wb_sel"] = 2
    elif op == 0x37:                             # lui
        c["reg_write"] = 1; c["wb_sel"] = 3
    elif op == 0x17:                             # auipc
        c["reg_write"] = 1; c["a_src_pc"] = 1; c["alu_src_imm"] = 1
    return c


def decode_aluop(op, f3, f7):
    """4-bit integer-ALU select for an instruction, matching seth_alu's encoding
    (0 ADD, 1 SUB, 2 SLL, 3 SLT, 4 SLTU, 5 XOR, 6 SRL, 7 SRA, 8 OR, 9 AND).

    R-type (0x33) decodes by funct3 with funct7=0x20 selecting SUB/SRA; the
    M-extension (funct7=0x01) doesn't use this ALU -> ADD. I-type ALU (0x13)
    decodes by funct3, with SRLI/SRAI distinguished by ins[30] (funct7=0x20). All
    other opcodes (loads/stores/branch/jalr/lui/auipc/jal/system) use the ALU only
    for address/PC arithmetic -> ADD."""
    op &= 0x7F
    f3 &= 0x7
    f7 &= 0x7F
    if op == 0x33:
        if f7 == 0x01:
            return 0
        if f3 == 0x0:
            return 1 if f7 == 0x20 else 0
        if f3 == 0x5:
            return 7 if f7 == 0x20 else 6
        return {0x1: 2, 0x2: 3, 0x3: 4, 0x4: 5, 0x6: 8, 0x7: 9}[f3]
    if op == 0x13:
        if f3 == 0x0:
            return 0
        if f3 == 0x5:
            return 7 if f7 == 0x20 else 6
        return {0x1: 2, 0x2: 3, 0x3: 4, 0x4: 5, 0x6: 8, 0x7: 9}[f3]
    return 0


def load_format(funct3, addr_lo, mem_word):
    """Word-addressed load formatting (mirrors seth_lsu / seth_core): select the
    byte/half at addr_lo within the aligned word and sign/zero-extend."""
    mem_word = u32(mem_word)
    boff = (addr_lo & 3) * 8
    shifted = mem_word >> boff
    f3 = funct3 & 0x7
    if f3 == 0x2:
        return mem_word                                    # lw
    if f3 == 0x1:
        return u32(_sext(shifted & 0xFFFF, 16))            # lh
    if f3 == 0x0:
        return u32(_sext(shifted & 0xFF, 8))               # lb
    if f3 == 0x5:
        return shifted & 0xFFFF                            # lhu
    if f3 == 0x4:
        return shifted & 0xFF                              # lbu
    return mem_word


def store_merge(funct3, addr_lo, mem_word, store_data):
    """Word-addressed store merge (mirrors seth_lsu / seth_core): returns
    (store_word, wstrb) — the read-modify-write word and per-byte strobe."""
    mem_word = u32(mem_word)
    store_data = u32(store_data)
    boff = (addr_lo & 3) * 8
    f3 = funct3 & 0x7
    if f3 == 0x0:                                          # sb
        mask = (0xFF << boff) & MASK
        sw = u32((mem_word & (~mask & MASK)) | ((store_data & 0xFF) << boff))
        return sw, (0b0001 << addr_lo) & 0xF
    if f3 == 0x1:                                          # sh
        mask = (0xFFFF << boff) & MASK
        sw = u32((mem_word & (~mask & MASK)) | ((store_data & 0xFFFF) << boff))
        return sw, (0b0011 << addr_lo) & 0xF
    return store_data, 0xF                                 # sw


def branch_taken(funct3, a, b):
    """RV32I conditional-branch test (mirrors Cpu._branch); invalid encodings
    (funct3 010/011) read as not-taken, matching seth_branch's default."""
    f3 = funct3 & 0x7
    if f3 == 0x0:
        return u32(a) == u32(b)
    if f3 == 0x1:
        return u32(a) != u32(b)
    if f3 == 0x4:
        return s32(a) < s32(b)
    if f3 == 0x5:
        return s32(a) >= s32(b)
    if f3 == 0x6:
        return u32(a) < u32(b)
    if f3 == 0x7:
        return u32(a) >= u32(b)
    return False


def csr_op(funct3, csr_in, rs1, zimm):
    """Zicsr CSR datapath. funct3: 1 RW, 2 RS, 3 RC, 5 RWI, 6 RSI, 7 RCI.

    Returns (rd_val, csr_out, csr_we): rd always gets the OLD csr value; CSRRW
    always writes; CSRRS/CSRRC write only when the operand is non-zero."""
    csr_in = u32(csr_in)
    operand = u32(zimm & 0x1F) if (funct3 & 0b100) else u32(rs1)
    low = funct3 & 0b011
    if low == 0b01:      # RW / RWI
        csr_out, we = operand, 1
    elif low == 0b10:    # RS / RSI
        csr_out, we = u32(csr_in | operand), (1 if operand != 0 else 0)
    elif low == 0b11:    # RC / RCI
        csr_out, we = u32(csr_in & ~operand), (1 if operand != 0 else 0)
    else:
        csr_out, we = csr_in, 0
    return (csr_in, csr_out, we)


class Cpu:
    def __init__(self):
        self.x = [0] * 32
        self.pc = 0
        self.mem = bytearray(64 * 1024)
        self.halted = False

    def _ld(self, addr, n):
        return int.from_bytes(self.mem[addr:addr + n], "little")

    def _st(self, addr, n, val):
        self.mem[addr:addr + n] = (val & ((1 << (8 * n)) - 1)).to_bytes(n, "little")

    def load(self, words, base=0):
        for i, w in enumerate(words):
            self._st(base + 4 * i, 4, w)
        self.pc = base

    def run(self, max_steps=100000):
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
        return self.x

    def step(self):
        ins = self._ld(self.pc, 4)
        op = ins & 0x7F
        rd = (ins >> 7) & 0x1F
        f3 = (ins >> 12) & 0x7
        rs1 = (ins >> 15) & 0x1F
        rs2 = (ins >> 20) & 0x1F
        f7 = (ins >> 25) & 0x7F
        npc = u32(self.pc + 4)
        a, b = self.x[rs1], self.x[rs2]

        if op == 0x33:        # R-type
            r = self._alu_r(f7, f3, a, b)
            self._wr(rd, r)
        elif op == 0x13:      # I-type ALU
            imm = _sext(ins >> 20, 12)
            if f3 == 0x1:
                r = u32(a << (imm & 0x1F))
            elif f3 == 0x5:
                r = u32(a >> (imm & 0x1F)) if (f7 == 0) else u32(s32(a) >> (imm & 0x1F))
            else:
                r = self._alu_i(f3, a, imm)
            self._wr(rd, r)
        elif op == 0x03:      # loads
            addr = u32(a + _sext(ins >> 20, 12))
            r = self._do_load(f3, addr)
            self._wr(rd, r)
        elif op == 0x23:      # stores
            imm = _sext(((f7 << 5) | rd), 12)
            addr = u32(a + imm)
            self._st(addr, {0: 1, 1: 2, 2: 4}[f3], b)
        elif op == 0x63:      # branches
            imm = _sext(((ins >> 31) << 12) | (((ins >> 7) & 1) << 11) |
                        (((ins >> 25) & 0x3F) << 5) | (((ins >> 8) & 0xF) << 1), 13)
            if self._branch(f3, a, b):
                npc = u32(self.pc + imm)
        elif op == 0x37:      # lui
            self._wr(rd, u32(ins & 0xFFFFF000))
        elif op == 0x17:      # auipc
            self._wr(rd, u32(self.pc + (ins & 0xFFFFF000)))
        elif op == 0x6F:      # jal
            imm = _sext(((ins >> 31) << 20) | (((ins >> 12) & 0xFF) << 12) |
                        (((ins >> 20) & 1) << 11) | (((ins >> 21) & 0x3FF) << 1), 21)
            self._wr(rd, npc)
            npc = u32(self.pc + imm)
        elif op == 0x67:      # jalr
            imm = _sext(ins >> 20, 12)
            t = u32((a + imm) & ~1)
            self._wr(rd, npc)
            npc = t
        elif op == 0x73:      # ecall/ebreak -> halt
            self.halted = True
        else:
            raise ValueError(f"unimplemented opcode 0x{op:02x} @ pc=0x{self.pc:x}")
        self.pc = npc

    def _wr(self, rd, val):
        if rd != 0:
            self.x[rd] = u32(val)

    def _alu_i(self, f3, a, imm):
        if f3 == 0x0:
            return u32(a + imm)
        if f3 == 0x2:
            return 1 if s32(a) < imm else 0
        if f3 == 0x3:
            return 1 if u32(a) < u32(imm) else 0
        if f3 == 0x4:
            return u32(a ^ imm)
        if f3 == 0x6:
            return u32(a | imm)
        if f3 == 0x7:
            return u32(a & imm)
        raise ValueError("bad I funct3")

    def _alu_r(self, f7, f3, a, b):
        if f7 == 0x01:        # M-extension
            return self._muldiv(f3, a, b)
        if f3 == 0x0:
            return u32(a - b) if f7 == 0x20 else u32(a + b)
        if f3 == 0x1:
            return u32(a << (b & 0x1F))
        if f3 == 0x2:
            return 1 if s32(a) < s32(b) else 0
        if f3 == 0x3:
            return 1 if u32(a) < u32(b) else 0
        if f3 == 0x4:
            return u32(a ^ b)
        if f3 == 0x5:
            return u32(s32(a) >> (b & 0x1F)) if f7 == 0x20 else u32(a >> (b & 0x1F))
        if f3 == 0x6:
            return u32(a | b)
        if f3 == 0x7:
            return u32(a & b)
        raise ValueError("bad R funct3")

    def _muldiv(self, f3, a, b):
        sa, sb = s32(a), s32(b)
        if f3 == 0x0:
            return u32(sa * sb)
        if f3 == 0x1:
            return u32((sa * sb) >> 32)
        if f3 == 0x2:
            return u32((sa * u32(b)) >> 32)
        if f3 == 0x3:
            return u32((u32(a) * u32(b)) >> 32)
        if f3 == 0x4:
            return MASK if sb == 0 else u32(_trunc_div(sa, sb))
        if f3 == 0x5:
            return MASK if b == 0 else u32(u32(a) // u32(b))
        if f3 == 0x6:
            return u32(sa) if sb == 0 else u32(_trunc_rem(sa, sb))
        if f3 == 0x7:
            return u32(a) if b == 0 else u32(u32(a) % u32(b))
        raise ValueError("bad M funct3")

    def _do_load(self, f3, addr):
        if f3 == 0x2:
            return self._ld(addr, 4)
        if f3 == 0x1:
            return u32(_sext(self._ld(addr, 2), 16))
        if f3 == 0x0:
            return u32(_sext(self._ld(addr, 1), 8))
        if f3 == 0x5:
            return self._ld(addr, 2)
        if f3 == 0x4:
            return self._ld(addr, 1)
        raise ValueError("bad load funct3")

    def _branch(self, f3, a, b):
        if f3 == 0x0:
            return u32(a) == u32(b)
        if f3 == 0x1:
            return u32(a) != u32(b)
        if f3 == 0x4:
            return s32(a) < s32(b)
        if f3 == 0x5:
            return s32(a) >= s32(b)
        if f3 == 0x6:
            return u32(a) < u32(b)
        if f3 == 0x7:
            return u32(a) >= u32(b)
        raise ValueError("bad branch funct3")


def _trunc_div(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def _trunc_rem(a, b):
    r = abs(a) % abs(b)
    return -r if a < 0 else r
