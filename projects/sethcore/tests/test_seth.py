import seth_rv32im as g
from seth_pipeline_model import Pipeline


def run(prog):
    cpu = g.Cpu()
    cpu.load(g.assemble(prog))
    return cpu.run()


def test_arith_program():
    # sum 1..10 in x1
    prog = [
        ("addi", 1, 0, 0),     # acc = 0
        ("addi", 2, 0, 1),     # i = 1
        ("addi", 3, 0, 11),    # limit = 11
        "loop:",
        ("add", 1, 1, 2),      # acc += i
        ("addi", 2, 2, 1),     # i++
        ("blt", 2, 3, "loop"),
        ("ecall",),
    ]
    x = run(prog)
    assert x[1] == 55


def test_fibonacci():
    # fib(10): x3 holds result
    prog = [
        ("addi", 1, 0, 0),     # a = 0
        ("addi", 2, 0, 1),     # b = 1
        ("addi", 4, 0, 10),    # n = 10
        ("addi", 5, 0, 0),     # i = 0
        "loop:",
        ("add", 3, 1, 2),      # c = a + b
        ("addi", 1, 2, 0),     # a = b
        ("addi", 2, 3, 0),     # b = c
        ("addi", 5, 5, 1),     # i++
        ("blt", 5, 4, "loop"),
        ("ecall",),
    ]
    x = run(prog)
    # fib sequence after 10 iterations: a = fib(10) = 55
    assert x[1] == 55


def test_mul_div():
    prog = [
        ("addi", 1, 0, 7),
        ("addi", 2, 0, -3 & 0xFFF),  # -3
        ("mul", 3, 1, 2),            # 7 * -3 = -21
        ("div", 4, 1, 2),            # 7 / -3 = -2 (trunc toward zero)
        ("rem", 5, 1, 2),            # 7 % -3 = 1
        ("ecall",),
    ]
    x = run(prog)
    assert g.s32(x[3]) == -21
    assert g.s32(x[4]) == -2
    assert g.s32(x[5]) == 1


def test_div_by_zero():
    prog = [("addi", 1, 0, 5), ("addi", 2, 0, 0),
            ("div", 3, 1, 2), ("rem", 4, 1, 2), ("ecall",)]
    x = run(prog)
    assert x[3] == 0xFFFFFFFF   # spec: div by zero -> all ones
    assert x[4] == 5            # rem by zero -> dividend


def test_branches():
    # exercise beq/bne/blt/bge selection
    prog = [
        ("addi", 1, 0, 5),
        ("addi", 2, 0, 5),
        ("addi", 10, 0, 0),
        ("bne", 1, 2, "skip"),   # not taken (equal)
        ("addi", 10, 10, 1),     # executed
        "skip:",
        ("bge", 1, 2, "done"),   # taken (5 >= 5)
        ("addi", 10, 10, 100),   # skipped
        "done:",
        ("ecall",),
    ]
    x = run(prog)
    assert x[10] == 1


def test_load_store():
    prog = [
        ("addi", 1, 0, 0x123 & 0xFFF),
        ("addi", 2, 0, 256),
        ("sw", 1, 0, 2),         # mem[256] = x1
        ("lw", 3, 0, 2),         # x3 = mem[256]
        ("ecall",),
    ]
    x = run(prog)
    assert x[3] == 0x123


def test_pymodel_equals_golden():
    prog = [
        ("addi", 1, 0, 0), ("addi", 2, 0, 1), ("addi", 3, 0, 11),
        "loop:", ("add", 1, 1, 2), ("addi", 2, 2, 1), ("blt", 2, 3, "loop"),
        ("ecall",),
    ]
    words = g.assemble(prog)
    gold = g.Cpu()
    gold.load(words)
    gx = gold.run()

    p = Pipeline()
    p.load(words)
    px = p.run()
    assert list(px) == list(gx)
    assert p.regs[1] == 55
    # cycles must exceed instruction count (branch bubbles add overhead)
    assert p.cycles > p.instructions


def test_decode_imm_formats():
    """decode_imm yields the correct sign-extended immediate per RV32 format,
    using the low-level field encoders to build instructions with raw immediates."""
    for imm in (0, 1, -1, 2047, -2048, 1365, -1366):
        assert g.decode_imm(g._I(imm, 1, 0x0, 5, 0x13)) == g.u32(imm)   # addi
        assert g.decode_imm(g._I(imm, 2, 0x2, 6, 0x03)) == g.u32(imm)   # lw
        assert g.decode_imm(g._I(imm, 2, 0x0, 1, 0x67)) == g.u32(imm)   # jalr
        assert g.decode_imm(g._S(imm, 7, 2, 0x2, 0x23)) == g.u32(imm)   # sw
    for imm in (0, 2, -2, 4094, -4096, 1024, -2048):                    # B: even, 13-bit
        assert g.decode_imm(g._B(imm, 2, 1, 0x0, 0x63)) == g.u32(imm)
    for imm in (0x00000000, 0x12345000, 0xABCDE000, 0xFFFFF000):        # U: upper 20
        assert g.decode_imm(g._U(imm, 5, 0x37)) == g.u32(imm)
        assert g.decode_imm(g._U(imm, 5, 0x17)) == g.u32(imm)
    for imm in (0, 2, -2, 0xFFFFE, -0x100000, 2048, -2048):             # J: even, 21-bit
        assert g.decode_imm(g._J(imm, 1, 0x6F)) == g.u32(imm)
    # R-type / system carry no immediate
    assert g.decode_imm(g._R(0, 3, 2, 0x0, 1, 0x33)) == 0
    assert g.decode_imm(g.assemble([("ecall",)])[0]) == 0


def _alu_sw(op, a, b):
    """Software mirror of seth_alu's 4-bit op encoding."""
    a &= 0xFFFFFFFF; b &= 0xFFFFFFFF; sh = b & 0x1F
    return {
        0: g.u32(a + b), 1: g.u32(a - b), 2: g.u32(a << sh),
        3: 1 if g.s32(a) < g.s32(b) else 0, 4: 1 if a < b else 0,
        5: g.u32(a ^ b), 6: g.u32(a >> sh), 7: g.u32(g.s32(a) >> sh),
        8: g.u32(a | b), 9: g.u32(a & b),
    }[op]


def test_decode_aluop_matches_execution():
    """decode_aluop + the ALU encoding reproduces the golden's R/I-type results."""
    import random
    rng = random.Random(9)
    vals = [0, 1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0xDEADBEEF, 1 << 20]
    for a in vals:
        for b in vals:
            # R-type: all funct3 with funct7 in {0x00, 0x20}
            for f3 in range(8):
                for f7 in (0x00, 0x20):
                    op = g.decode_aluop(0x33, f3, f7)
                    assert _alu_sw(op, a, b) == g.u32(g.Cpu()._alu_r(f7, f3, a, b)), (f3, f7)
            # I-type ALU: shift amount in b[4:0]; non-shift uses imm = b
            for f3 in range(8):
                if f3 in (0x1, 0x5):
                    f7 = 0x20 if (f3 == 0x5 and (b & 1)) else 0x00
                    op = g.decode_aluop(0x13, f3, f7)
                    exp = g.u32(g.s32(a) >> (b & 0x1F)) if (f3 == 0x5 and f7 == 0x20) else (
                        g.u32(a << (b & 0x1F)) if f3 == 0x1 else g.u32(a >> (b & 0x1F)))
                    assert _alu_sw(op, a, b) == exp, ("I", f3, f7)
                else:
                    op = g.decode_aluop(0x13, f3, 0)
                    assert _alu_sw(op, a, b) == g.u32(g.Cpu()._alu_i(f3, a, g.s32(b))), ("I", f3)
    # non-ALU opcodes default to ADD
    for op in (0x03, 0x23, 0x63, 0x67, 0x37, 0x17, 0x6F, 0x73):
        assert g.decode_aluop(op, 0, 0) == 0


def test_decode_ctrl_matches_step():
    """decode_ctrl's reg_write/mem_write/branch/jump agree with Cpu.step behaviour."""
    samples = {
        0x33: g._R(0x00, 3, 2, 0x0, 5, 0x33),     # add  x5,x1?,..
        0x13: g._I(7, 1, 0x0, 5, 0x13),           # addi x5,x1,7
        0x03: g._I(4, 2, 0x2, 6, 0x03),           # lw   x6,4(x2)
        0x23: g._S(8, 7, 2, 0x2, 0x23),           # sw   x7,8(x2)
        0x63: g._B(0, 2, 1, 0x0, 0x63),           # beq  x1,x2
        0x67: g._I(0, 2, 0x0, 1, 0x67),           # jalr x1,x2
        0x6F: g._J(0, 1, 0x6F),                   # jal  x1
        0x37: g._U(0x12345000, 5, 0x37),          # lui  x5
        0x17: g._U(0x1000, 5, 0x17),              # auipc x5
        0x73: g.assemble([("ecall",)])[0],        # system
    }
    for op, ins in samples.items():
        c = g.decode_ctrl(ins)
        rd = (ins >> 7) & 0x1F
        # behavioural cross-checks against a fresh CPU executing this one instruction
        cpu = g.Cpu(); cpu.mem[0:4] = ins.to_bytes(4, "little")
        cpu.x[1] = 0x100; cpu.x[2] = 0x200; cpu.x[3] = 0x55
        before = list(cpu.x)
        try:
            cpu.step()
        except Exception:
            pass
        # no-write opcodes must leave every register untouched; the rest set reg_write
        if op in (0x63, 0x23, 0x73):
            assert c["reg_write"] == 0
            assert cpu.x == before, f"op {op:#x} unexpectedly wrote a register"
        else:
            assert c["reg_write"] == 1
    # field-level spot checks
    assert g.decode_ctrl(samples[0x03])["mem_read"] == 1
    assert g.decode_ctrl(samples[0x23])["mem_write"] == 1
    assert g.decode_ctrl(samples[0x63])["branch"] == 1
    assert g.decode_ctrl(samples[0x6F])["jump"] == 1 and g.decode_ctrl(samples[0x6F])["jalr"] == 0
    assert g.decode_ctrl(samples[0x67])["jalr"] == 1
    assert g.decode_ctrl(samples[0x37])["wb_sel"] == 3
    assert g.decode_ctrl(samples[0x17])["a_src_pc"] == 1
    assert g.decode_ctrl(g._R(0x01, 3, 2, 0x0, 5, 0x33))["is_mdu"] == 1   # M-ext


def test_branch_taken():
    assert g.branch_taken(0b000, 5, 5) is True            # beq
    assert g.branch_taken(0b001, 5, 5) is False           # bne
    assert g.branch_taken(0b100, 0xFFFFFFFF, 1) is True   # blt: -1 < 1 signed
    assert g.branch_taken(0b110, 0xFFFFFFFF, 1) is False  # bltu: big > 1 unsigned
    assert g.branch_taken(0b101, 1, 0xFFFFFFFF) is True   # bge: 1 >= -1 signed
    assert g.branch_taken(0b111, 1, 0xFFFFFFFF) is False  # bgeu: 1 < big unsigned
    assert g.branch_taken(0b111, 5, 5) is True            # bgeu equal
    assert g.branch_taken(0b010, 5, 5) is False           # invalid -> not taken


def test_csr_op():
    # RW always writes; rd gets old value
    assert g.csr_op(0b001, 0xAAAA, 0x1234, 0) == (0xAAAA, 0x1234, 1)
    # RWI uses 5-bit zimm
    assert g.csr_op(0b101, 0xAAAA, 0xFFFFFFFF, 0x1F) == (0xAAAA, 0x1F, 1)
    # RS sets bits; no write when operand 0
    assert g.csr_op(0b010, 0xF0, 0x0F, 0) == (0xF0, 0xFF, 1)
    assert g.csr_op(0b010, 0xF0, 0, 0) == (0xF0, 0xF0, 0)
    # RC clears bits; no write when operand 0
    assert g.csr_op(0b011, 0xFF, 0x0F, 0) == (0xFF, 0xF0, 1)
    assert g.csr_op(0b111, 0xFF, 0, 0) == (0xFF, 0xFF, 0)
