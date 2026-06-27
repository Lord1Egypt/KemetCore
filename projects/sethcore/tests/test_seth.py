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
