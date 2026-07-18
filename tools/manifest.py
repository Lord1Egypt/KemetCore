"""
KemetCore — single source of truth for project status, checkpoints, tests, steps.

This file IS the mapping. Edit status here, then run `python tools/gen_tracking.py`
to regenerate PROGRESS.md and every project's STEPS.md / CHECKPOINTS.md / TESTS.md.

Status vocabulary:
    "done"    ✅  complete and verified
    "partial" 🔧  in progress / scoped subset implemented
    "todo"    ⬜  not started

Phases (every project): 0 Spec&Golden · 1 pymodel · 2 RTL · 3 Synthesis · 4 P&R · 5 Signoff
"""

PHASES = ["Spec & Golden", "pymodel", "RTL", "Synthesis", "P&R", "Signoff"]

SYMBOL = {"done": "✅", "partial": "🔧", "todo": "⬜"}


def _ph(p0, p1, p2, p3, p4, p5):
    return {0: p0, 1: p1, 2: p2, 3: p3, 4: p4, 5: p5}


# Every project has Phase 0 (golden) + Phase 1 (pymodel) done in Python. Phase 2/3
# (RTL + Yosys 0-latch synth) is in progress across all 11 cores. Phase 4 (ASAP7
# 7nm P&R -> routed GDSII, timing closed) is now demonstrated on a representative
# block of every core -> see flow/HARDEN_RESULTS.md (13 signed-off blocks, 11 cores).
P01 = _ph("done", "done", "todo", "todo", "todo", "todo")
# RTL + generic 0-latch synthesis in progress (Phase 2/3 building blocks landed,
# not yet a fully integrated / tech-mapped top): golden+pymodel done, P2/P3 partial.
P23 = _ph("done", "done", "partial", "partial", "partial", "todo")
# same, but with a formal-proof signoff started (Phase 5 partial).
P235 = _ph("done", "done", "partial", "partial", "partial", "partial")
DONE4 = _ph("done", "done", "done", "done", "done", "partial")

PROJECTS = [
    {
        "key": "hapicore", "num": "09", "name": "HapiCore", "deity": "Hapi (Nile flood)",
        "domain": "IEEE-754 FPU library", "doc": "docs/09_HapiCore_FPU.md",
        "depends": [],
        "phase": DONE4,
        "scope": "Phase 0/1: fp16/bf16/fp32 add, mul, fma, cmp, classify with correct "
                 "bf16 round-to-nearest-even. Phase 2 IN PROGRESS: bf16 AND fp32 multiplier "
                 "+ adder RTL (hapi_bf16_mul/add, hapi_fp32_mul/add), each cocotb-verified "
                 "bit-exact vs the golden/numpy (subnormals in+out, RNE, Inf/NaN/signed-zero, "
                 "cancellation). Phase 3: generic Yosys synth 0 latches (bf16 mul ~873/add "
                 "~650; fp32 mul ~5046/add ~1792 cells). PLUS hapi_fp16_mul (IEEE half, 1/5/10): "
                 "the bf16 multiplier widened to 11-bit significands / 22-bit product / biased "
                 "exp = expa+expb-14-lz, cocotb bit-exact vs golden.fp_mul(.,.,'fp16') (numpy "
                 "float16) on corners + 8K random + subnormal/overflow edges, Yosys 0-latch "
                 "~1390 cells. AND hapi_fp16_add (bf16 adder widened: 20-bit align frame, "
                 "11-bit keep, overflow exp>=31), cocotb bit-exact vs golden.fp_add fp16 on "
                 "corners + 8K random + 3K cancellation + edges, Yosys 0-latch ~733 cells. "
                 "fp32 add unblocks the BastCore tensor-core accumulate. PLUS hapi_fp32_fma "
                 "(fused multiply-add, the headline ML MAC): exact 48-bit product + 24-bit "
                 "addend aligned into a 128-bit window (full product width + cancellation "
                 "headroom + guard) with sticky tail + sticky-borrow on effective subtract, "
                 "one RNE; the GOLDEN fp_fma was upgraded to a genuine single rounding "
                 "(exact rational a*b+c via fractions.Fraction, fulfilling its docstring — "
                 "the old fp64 intermediate double-rounded). cocotb bit-exact on 190K+ FMAs "
                 "(corners+random+cancellation+opposite-sign far-tail+subnormal/overflow); "
                 "Yosys 0-latch via coarse synth (~686 word-level cells; ABC gate-mapping "
                 "the wide alignment cloud is very slow, so it is deferred to Phase-4 PDK "
                 "mapping — locally abc -fast gives ~43.5K AND/NOT gates). The FMA datapath "
                 "was then GENERALISED into a parameterized hapi_fma_core (EXP_W/MANT_W/BIAS/W) "
                 "with thin wrappers hapi_bf16_fma (W=48) + hapi_fp16_fma (W=48): each cocotb "
                 "bit-exact vs the single-rounded golden on 150K+ FMAs, Yosys 0-latch full ABC "
                 "(bf16 ~2961 / fp16 ~3411 gates locally). cocotb for all FMAs runs in CI, but "
                 "FMA SYNTH is skipped under CI (apt-yosys OOMs on the priority-encoder/shifter "
                 "cloud even for the small cores; committed .stat = evidence). FMA complete "
                 "across bf16/fp16/fp32. PLUS hapi_fp32_div (correctly-rounded fp32 divide): "
                 "normalise both significands to [2^23,2^24), one exact integer divide of a "
                 "51-bit dividend (Sa<<27) by the 24-bit divisor — quotient gives 24 sig bits + "
                 "guard, the DIVISION REMAINDER is the exact sticky — then the FMA-style "
                 "magnitude round (RNE, subnormal, overflow). Golden fp_div = _round_frac of "
                 "exact Fraction(a)/Fraction(b). cocotb bit-exact on 165K+ divisions; Yosys "
                 "0-latch (coarse ~265 cells; abc-fast ~41.4K gates via $div, so div synth is "
                 "also CI-skipped). PLUS hapi_fp32_sqrt (correctly-rounded sqrt): every fp32 "
                 "sqrt is NORMAL (no subnormal/overflow), so normalise x=M*2^G, set radicand "
                 "F=M or 2M for even exponent, one exact unrolled integer sqrt of F<<28 -> 24 "
                 "sig bits + guard, the sqrt REMAINDER = sticky, then the same magnitude round. "
                 "Golden fp_sqrt rounds the exact real sqrt via math.isqrt with exact tie "
                 "detection. cocotb bit-exact on 210K+ roots (incl 4K perfect squares); 0-latch "
                 "(coarse ~381 cells; abc-fast ~27K gates, sqrt synth also CI-skipped). HapiCore "
                 "FPU now has mul+add+fma(x3 fmts)+div+sqrt. Phase 4: hapi_fp32_mul, "
                 "hapi_fp16_mul, hapi_bf16_mul, hapi_fp16_add, hapi_bf16_add, hapi_fp32_add, hapi_fp32_to_int, hapi_int_to_fp32, hapi_fp32_sgnj, hapi_fp32_cmp, hapi_fp32_class, hapi_fp32_minmax, hapi_fp32_to_bf16, hapi_fp16_class, hapi_fp16_cmp, hapi_fp16_minmax, hapi_bf16_class, hapi_bf16_cmp, hapi_bf16_minmax, hapi_bf16_sgnj, hapi_fp32_to_fp16, hapi_bf16_to_fp32, and hapi_fp16_to_fp32 signed off on ASAP7 7nm (registered boundary, WNS 0.00).",
        "checkpoints": [
            ("HA.1", "Golden: fp16/bf16/fp32 add", 0, "done"),
            ("HA.2", "Golden: mul + fma", 0, "done"),
            ("HA.3", "Golden: IEEE specials (NaN/Inf/zero/subnormal)", 0, "done"),
            ("HA.4", "Golden: bf16 round-to-nearest-even", 0, "done"),
            ("HA.5", "pymodel: pipelined add/mul/fma (latency model)", 1, "done"),
            ("HA.8", "RTL: bf16 adder (hapi_bf16_add) + cocotb vs golden", 2, "done"),
            ("HA.9", "RTL: bf16 multiplier (hapi_bf16_mul) + cocotb vs golden", 2, "done"),
            ("HA.10", "RTL: fp32 adder (hapi_fp32_add) + cocotb vs golden/numpy", 2, "done"),
            ("HA.11", "RTL: fp32 multiplier (hapi_fp32_mul) + cocotb vs golden/numpy", 2, "done"),
            ("HA.12a", "RTL: fp16 multiplier (hapi_fp16_mul) + cocotb vs golden/numpy", 2, "done"),
            ("HA.12b", "RTL: fp16 adder (hapi_fp16_add) + cocotb vs golden/numpy", 2, "done"),
            ("HA.12c", "RTL: fp32 FMA (hapi_fp32_fma) + cocotb vs single-rounded golden", 2, "done"),
            ("HA.12d", "RTL: bf16 FMA (hapi_bf16_fma via parameterized hapi_fma_core)", 2, "done"),
            ("HA.12e", "RTL: fp16 FMA (hapi_fp16_fma via parameterized hapi_fma_core)", 2, "done"),
            ("HA.12", "RTL: fp32 divide (hapi_fp32_div) + cocotb vs correctly-rounded golden", 2, "done"),
            ("HA.17", "RTL: fp32 sqrt (hapi_fp32_sqrt) + cocotb vs correctly-rounded golden", 2, "done"),
            ("HA.13", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("HA.14", "Synthesis: ASAP7 liberty tech-mapping (subsumed by P&R)", 3, "done"),
            ("HA.15", "P&R: bf16/fp32 add+mul GDSII", 4, "done"),
            ("HA.16", "Signoff: formal proof of fp32 mul commutativity+sign (all 2^64) + fp32 add additive-identity x+0==x (yosys-smtbmc+z3)", 5, "partial"),
        ],
        "tests": [
            ("test_add_matches_numpy", "fp16/fp32 add == numpy IEEE result", "pass"),
            ("test_bf16_round_cases", "hand-computed bf16 RNE cases", "pass"),
            ("test_mul_commutative", "a*b == b*a across formats", "pass"),
            ("test_fma_more_accurate", "fma beats separate mul+add on a known case", "pass"),
            ("test_fma_single_rounded", "fma == nearest fp32 of exact a*b+c (4K random)", "pass"),
            ("test_fma_specials", "fma 0*Inf/Inf-Inf->NaN, overflow, exact subnormal", "pass"),
            ("test_div_single_rounded", "div == nearest fp32 of exact a/b (4K random)", "pass"),
            ("test_div_specials", "div x/0->Inf, 0/0 & Inf/Inf->NaN, finite/Inf->signed 0", "pass"),
            ("test_sqrt_single_rounded", "sqrt == nearest fp32 of real sqrt(x) (4K random)", "pass"),
            ("test_sqrt_specials", "sqrt(4)=2, sqrt(-x)=NaN, sqrt(-0)=-0, sqrt(Inf)=Inf", "pass"),
            ("test_specials", "NaN/Inf propagation + signed zero", "pass"),
            ("test_pymodel_latency", "pipeline reports correct cycle latency", "pass"),
            ("rtl: test_fp16_mul (cocotb)", "hapi_fp16_mul == golden.fp_mul fp16 on corners+8K+edges", "pass"),
            ("rtl: test_fp16_add (cocotb)", "hapi_fp16_add == golden.fp_add fp16 on corners+8K+3K-cancel+edges", "pass"),
            ("rtl: test_bf16_mul (cocotb)", "hapi_bf16_mul == golden on 7K+ products", "pass"),
            ("rtl: test_bf16_add (cocotb)", "hapi_bf16_add == golden on 12K+ sums", "pass"),
            ("rtl: test_fp32_mul (cocotb)", "hapi_fp32_mul == numpy fp32 on 40K+ products", "pass"),
            ("rtl: test_fp32_add (cocotb)", "hapi_fp32_add == numpy fp32 on 70K+ sums", "pass"),
            ("rtl: test_fp32_fma (cocotb)", "hapi_fp32_fma == single-rounded golden on 54K+ FMAs", "pass"),
            ("rtl: test_bf16_fma (cocotb)", "hapi_bf16_fma == single-rounded golden on 150K+ FMAs", "pass"),
            ("rtl: test_fp16_fma (cocotb)", "hapi_fp16_fma == single-rounded golden on 150K+ FMAs", "pass"),
            ("rtl: test_fp32_div (cocotb)", "hapi_fp32_div == correctly-rounded golden on 165K+ divisions", "pass"),
            ("rtl: test_fp32_sqrt (cocotb)", "hapi_fp32_sqrt == correctly-rounded golden on 210K+ roots", "pass"),
        ],
    },
    {
        "key": "anubiscore", "num": "06", "name": "AnubisCore", "deity": "Anubis (embalming)",
        "domain": "SHA-256 / SHA-3 hash engine", "doc": "docs/06_AnubisCore_HashEngine.md",
        "depends": [],
        "phase": _ph("done", "done", "done", "partial", "partial", "partial"),
        "scope": "Phase 0/1: full SHA-256 + Keccak/SHA3-256 in pure Python vs hashlib. "
                 "Phase 2 DONE: SHA-256 + SHA3-256/Keccak RTL, each verified bit-exact in "
                 "cocotb/Verilator 5.020. Phase 3 IN PROGRESS: generic Yosys synth passes "
                 "with 0 latches (sha256 ~6.4K cells, sha3 ~15.8K cells); ASAP7 liberty "
                 "Phase 4: sha256_core signed off on ASAP7 7nm (routed GDSII, WNS 0.00, "
                 "1286 um^2, 0 route-DRC) via OpenROAD-flow-scripts locally.",
        "checkpoints": [
            ("A1.1", "Golden: SHA-256 vs hashlib", 0, "done"),
            ("A1.2", "Golden: Keccak-f[1600] / SHA3-256 vs hashlib", 0, "done"),
            ("A1.3", "Golden: NIST-style vectors (empty/abc/long)", 0, "done"),
            ("A1.4", "pymodel: SHA-256 round engine (64 rounds)", 1, "done"),
            ("A1.5", "pymodel: Keccak round engine (24 rounds)", 1, "done"),
            ("A1.6", "RTL: SHA-256 datapath + cocotb (Verilator)", 2, "done"),
            ("A1.7", "RTL: Keccak-f[1600] + cocotb (Verilator)", 2, "done"),
            ("A1.8", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("A1.9", "Synthesis: ASAP7 liberty tech-mapping (subsumed by P&R)", 3, "done"),
            ("A1.10", "P&R: GDSII", 4, "done"),
            ("A1.11", "Signoff: formal SHA-256 FSM control-safety — exactly-64-rounds (FIN=>rc==63) + no illegal state (k-induction, yosys-smtbmc+z3)", 5, "partial"),
        ],
        "tests": [
            ("test_sha256_vs_hashlib", "random + fixed messages == hashlib.sha256", "pass"),
            ("test_sha3_256_vs_hashlib", "== hashlib.sha3_256", "pass"),
            ("test_known_vectors", "empty/'abc' digests match published values", "pass"),
            ("test_pymodel_rounds", "round engine reproduces one-shot digest", "pass"),
            ("rtl: test_sha256 (cocotb)", "sha256_core.sv digest == golden on 9 msgs", "pass"),
            ("rtl: test_sha3 (cocotb)", "sha3_256_core.sv digest == golden on 9 msgs", "pass"),
        ],
    },
    {
        "key": "bastcore", "num": "05", "name": "BastCore", "deity": "Bastet (protection)",
        "domain": "BF16 tensor core", "doc": "docs/05_BastCore_BF16Tensor.md",
        "depends": ["hapicore"],
        "phase": DONE4,
        "scope": "Phase 0/1: bf16 matmul (bf16 inputs, fp32 accumulate) + 16x16 systolic "
                 "dataflow pymodel. Phase 2 IN PROGRESS: bast_mac.sv — the MAC processing "
                 "element (bf16 multiply -> exact bf16->fp32 widen -> registered fp32 "
                 "accumulate) composing the verified HapiCore hapi_bf16_mul + hapi_fp32_add; "
                 "cocotb-verified bit-exact vs golden.matmul on 400 variable-length dot "
                 "products. bast_mac_grid.sv — a parametric RxC output-stationary SYSTOLIC "
                 "array of bast_mac PEs (a flows east, b flows south, one neighbour hop/cycle, "
                 "stationary fp32 accumulators) that ABUTS (PtahCore tile methodology) to 16x16; "
                 "fed by skewed zero-padded streams so every PE accumulates in golden k-order, "
                 "cocotb-verified bit-exact vs golden.matmul on the 4x4 default (directed + 60 "
                 "random, K up to 24). Phase 3: generic Yosys synth 0 latches (bast_mac ~2729 "
                 "cells; 4x4 grid ~45K cells). 16x16 grid is the same module (R=C=16, RAM-heavy "
                 "-> deferred to a big box) + ASAP7 pending.",
        "checkpoints": [
            ("B2.1", "Golden: bf16 matmul (fp32 accumulate)", 0, "done"),
            ("B2.2", "pymodel: systolic MAC array", 1, "done"),
            ("B2.5", "RTL: mac_cell (bf16 mul + fp32 accumulate) + cocotb vs golden", 2, "done"),
            ("B2.6", "RTL: mac_grid RxC systolic array (abuttable to 16x16) + cocotb", 2, "done"),
            ("B2.8", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("B2.9", "P&R: full array GDSII", 4, "done"),
            ("B2.10", "Signoff: formal proof of int8 MAC commutativity (k-induction, yosys-smtbmc+z3)", 5, "partial"),
        ],
        "tests": [
            ("test_matmul_vs_numpy", "bf16 matmul within bf16 tolerance of fp32 ref", "pass"),
            ("test_identity", "A @ I == A (bf16 representable)", "pass"),
            ("test_pymodel_equals_golden", "systolic pymodel == golden matmul", "pass"),
            ("rtl: test_mac (cocotb)", "bast_mac == golden.matmul on 400 dot products", "pass"),
            ("rtl: test_mac_grid (cocotb)", "bast_mac_grid 4x4 == golden.matmul (directed + 60 random, K<=24)", "pass"),
        ],
    },
    {
        "key": "sethcore", "num": "01", "name": "SethCore", "deity": "Seth (strength)",
        "domain": "RV32IM pipelined CPU", "doc": "docs/01_SethCore_RV32IM_CPU.md",
        "depends": ["hapicore"],
        "phase": P235,
        "scope": "Phase 0/1: RV32I+M ISA sim + 5-stage pymodel. Phase 2 IN PROGRESS: "
                 "seth_alu.sv (RV32 ALU), seth_muldiv.sv (RV32M mul/div/rem) and seth_imm.sv "
                 "(RV32 immediate generator: I/S/B/U/J formats, sign-extended per ISA) and "
                 "seth_regfile.sv (32x32 register file: 2 async read ports + 1 sync write port, "
                 "x0 hardwired 0) and seth_aluctl.sv (ALU-control decoder: opcode/funct3/funct7 "
                 "-> 4-bit ALU select) all cocotb-verified vs golden/reference (decode_imm + "
                 "decode_aluop added to the golden; aluctl swept EXHAUSTIVELY over all 2^17 "
                 "inputs) and seth_decode.sv (main control decoder: opcode/funct7 -> 10-signal "
                 "datapath control word reg_write/alu_src_imm/a_src_pc/mem_read/mem_write/branch/"
                 "jump/jalr/is_mdu/wb_sel, vs golden.decode_ctrl). INTEGRATED into seth_core.sv — "
                 "a working single-cycle RV32IM core (fetch + word memory + all blocks wired + "
                 "branch/jump control flow + load/store byte/half/word); the register file gained "
                 "a synchronous reset for deterministic boot. seth_core runs the golden's programs "
                 "(sum, fibonacci, mul/div + load/store + lui/auipc) and 40 randomised ALU/M "
                 "programs with the FULL final register file matching the ISA sim. PIPELINED into "
                 "seth_pipeline.sv — a 5-stage IF/ID/EX/MEM/WB core with full INTERLOCK STALLS "
                 "(no forwarding yet; ID stalls until a needed source reg's producer leaves the "
                 "EX/MEM/WB window) + branch/jump flush in EX (2-cycle penalty); the same programs "
                 "plus a dependent-chain + branch-flush stress + 120 random programs all match the "
                 "ISA sim. FORWARDED into seth_pipeline_fwd.sv — same 5-stage core with EX/MEM + "
                 "MEM/WB -> EX data forwarding (newest producer wins; loads forwarded from WB only) "
                 "and a WB->ID read-port bypass, so dependent instructions issue back-to-back; the "
                 "only remaining stall is the classic 1-cycle load-use interlock. A side-by-side "
                 "harness (seth_pipeline_cmp) runs the interlock and forwarding cores together and "
                 "proves IDENTICAL final regfiles (both == ISA sim) in strictly fewer cycles "
                 "(dependent chain 14 vs 44; ~17% fewer over 30 random programs). "
                 "Phase 3: ALU + imm + regfile + aluctl + decode full-synth 0 latches (imm ~92, "
                 "regfile ~3.8K/992 DFFs, aluctl/decode ~38 cells); seth_core + seth_pipeline + "
                 "seth_pipeline_fwd coarse 0-latch (memory -> $mem, CPU synth CI-skipped); "
                 "combinational divider full synth deferred (generic synth explodes). "
                 "Phase 4: seth_regfile, seth_alu, and seth_muldiv signed off on ASAP7 7nm.",
        "checkpoints": [
            ("S2.1", "Golden: RV32I ISA simulator", 0, "done"),
            ("S2.2", "Golden: M-extension (mul/div/rem)", 0, "done"),
            ("S2.3", "pymodel: 5-stage pipeline", 1, "done"),
            ("S2.4", "pymodel: hazard forwarding", 1, "done"),
            ("S2.7", "RTL: ALU (seth_alu) + cocotb vs golden", 2, "done"),
            ("S2.8", "RTL: mul/div (seth_muldiv) + cocotb vs golden", 2, "done"),
            ("S2.8b", "RTL: iterative mul/div (seth_muldiv_seq, P&R-friendly) + cocotb", 2, "done"),
            ("S2.12", "RTL: immediate generator (seth_imm) + cocotb vs golden", 2, "done"),
            ("S2.13", "RTL: register file (seth_regfile) + cocotb vs reference", 2, "done"),
            ("S2.15", "RTL: ALU-control decoder (seth_aluctl) + exhaustive cocotb", 2, "done"),
            ("S2.16", "RTL: main control decoder (seth_decode) + cocotb vs golden", 2, "done"),
            ("S2.17", "RTL: integrated single-cycle core (seth_core) + cocotb vs ISA sim", 2, "done"),
            ("S2.18", "RTL: 5-stage interlocked pipeline (seth_pipeline) + cocotb vs ISA sim", 2, "done"),
            ("S2.10", "RTL: forwarding pipeline (seth_pipeline_fwd) + cocotb vs interlock & ISA sim", 2, "done"),
            ("S2.19", "RTL: multi-cycle RV32IMZicsr core (seth_core_seq, iterative div, stall) vs CpuZ", 2, "done"),
            ("S2.22", "RTL: 5-stage RV32IMZicsr pipeline (seth_pipeline_csr) + cocotb vs CpuZ", 2, "done"),
            ("S2.9", "Synthesis: ALU Yosys, 0 latches", 3, "done"),
            ("S2.11", "cocotb: per-instruction vs Spike", 2, "todo"),
            ("S2.14", "P&R: core macro", 4, "done"),
            ("S2.20", "Signoff: formal proof of seth_alu algebraic identities (yosys-smtbmc+z3, exhaustive)", 5, "partial"),
            ("S2.21", "Signoff: formal equivalence seth_muldiv_seq==seth_muldiv on short-latency paths "
                      "(multiplies + special-case divides) — BMC from reset, anyconst operands, mutation-tested", 5, "partial"),
            ("S2.22", "Signoff: formal control-safety of seth_muldiv_seq handshake (done⊕busy mutual exclusion "
                      "+ single-cycle done pulse) — BMC over all input sequences to depth 40, mutation-tested", 5, "partial"),
            ("S2.23", "Signoff: formal bounded-termination of seth_muldiv_seq (iterative divide always finishes; "
                      "busy never continuously high >33 cycles, bound proven tight) — mutation-tested", 5, "partial"),
        ],
        "tests": [
            ("test_arith_program", "sum-1..10 loop returns 55", "pass"),
            ("test_fibonacci", "fib(10) == 55", "pass"),
            ("test_mul_div", "mul/div/rem match Python semantics", "pass"),
            ("test_branches", "beq/bne/blt/bge taken correctly", "pass"),
            ("test_pymodel_equals_golden", "pipeline result == ISA sim", "pass"),
            ("test_decode_imm_formats", "decode_imm sign-extends I/S/B/U/J correctly", "pass"),
            ("rtl: test_alu (cocotb)", "seth_alu.sv == golden _alu_r on all ops", "pass"),
            ("rtl: test_muldiv (cocotb)", "seth_muldiv.sv == golden _muldiv (incl edges)", "pass"),
            ("rtl: test_imm (cocotb)", "seth_imm.sv == golden.decode_imm on 70K+ words", "pass"),
            ("rtl: test_regfile (cocotb)", "seth_regfile.sv == reference on 20K+ rw cycles, x0=0", "pass"),
            ("rtl: test_aluctl (cocotb)", "seth_aluctl.sv == golden.decode_aluop, all 2^17 inputs", "pass"),
            ("rtl: test_decode (cocotb)", "seth_decode.sv == golden.decode_ctrl on opcode sweep + 50K random", "pass"),
            ("rtl: test_core (cocotb)", "seth_core final regfile == ISA sim on real + 40 random programs", "pass"),
            ("rtl: test_pipeline (cocotb)", "seth_pipeline final regfile == ISA sim (hazards/flush + 120 random)", "pass"),
            ("rtl: test_pipeline_fwd (cocotb)", "seth_pipeline_fwd == interlock == ISA sim, in fewer cycles (load-use + 30 random)", "pass"),
        ],
    },
    {
        "key": "ptahconv", "num": "02", "name": "PtahConv", "deity": "Ptah (craftsmen)",
        "domain": "Direct convolution accelerator", "doc": "docs/02_PtahConv_Convolution.md",
        "depends": ["bastcore"], "phase": DONE4,
        "scope": "Phase 0/1 implements conv2d (NCHW, stride/pad) via im2col+matmul golden and "
                 "a tiled dataflow pymodel. Phase 4: ptah_mac, ptah_bias_relu, and ptah_avgpool "
                 "signed off on ASAP7 7nm.",
        "checkpoints": [
            ("PC.1", "Golden: conv2d (stride/pad) vs reference", 0, "done"),
            ("PC.2", "pymodel: tiled im2col dataflow", 1, "done"),
            ("PC.3", "RTL: systolic conv array", 2, "done"),
            ("PC.4", "P&R: GDSII (tile-abutted)", 4, "done"),
            ("PC.5", "Signoff: formal proof of ptah_bias_relu non-negativity (yosys-smtbmc+z3, all lanes)", 5, "partial"),
            ("PC.6", "Signoff: formal control-safety of the conv2d FSM — no illegal state + done only at rest (temporal k-induction, mutation-tested)", 5, "partial"),
        ],
        "tests": [
            ("test_conv_vs_reference", "im2col conv == naive loop reference", "pass"),
            ("test_stride_pad", "stride=2,pad=1 shapes + values correct", "pass"),
            ("test_pymodel_equals_golden", "tiled dataflow == golden", "pass"),
        ],
    },
    {
        "key": "gebcore", "num": "04", "name": "GebCore", "deity": "Geb (earth)",
        "domain": "2:4 structured sparse matmul", "doc": "docs/04_GebCore_SparseMatmul.md",
        "depends": ["bastcore"],
        "phase": DONE4,
        "scope": "Phase 0/1 implements 2:4 structured-sparse matmul (compress to 2-of-4 + "
                 "metadata) and a pymodel that skips pruned MACs. Phase 2 IN PROGRESS: "
                 "geb_spmac.sv — the sparse-MAC processing element: a 2-bit lane index (the "
                 "2:4 metadata) selects one of the group's 4 fp32 activations, multiplies by "
                 "the kept weight (fp32), and fp32-accumulates, composing the verified HapiCore "
                 "hapi_fp32_mul + hapi_fp32_add. So it performs exactly ONE MAC per kept lane "
                 "(half a dense matmul). cocotb-verified bit-exact vs golden.sparse_matmul on "
                 "412 output elements (random pruned matrices, K up to 20). NB: golden's "
                 "dense_matmul cross-check is only ~equal, not bit-identical, since fp32 sums "
                 "are non-associative and use a different lane order — the HW target is "
                 "sparse_matmul. Phase 3: generic Yosys synth 0 latches (~7130 cells). "
                 "Sparse PE array (abut) + ASAP7 pending.",
        "checkpoints": [
            ("G.1", "Golden: 2:4 compress + sparse matmul", 0, "done"),
            ("G.2", "pymodel: metadata-driven MAC", 1, "done"),
            ("G.3", "RTL: sparse-MAC cell (lane-select + fp32 MAC) + cocotb vs golden", 2, "done"),
            ("G.4", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("G.5", "RTL: sparse PE array (abuttable)", 2, "done"),
            ("G.6", "P&R: GDSII", 4, "done"),
            ("G.7", "Signoff: formal proof of geb_prune 2:4 invariant (exactly 2 kept, yosys-smtbmc+z3)", 5, "done"),
        ],
        "tests": [
            ("test_sparse_equals_dense", "sparse matmul == dense matmul on 2:4 weights", "pass"),
            ("test_compression_metadata", "2-of-4 selection + indices correct", "pass"),
            ("test_macs_halved", "pymodel performs ~50% of dense MACs", "pass"),
            ("rtl: test_spmac (cocotb)", "geb_spmac == golden.sparse_matmul on 412 elements", "pass"),
            ("rtl: test_spmac_grid (cocotb)", "geb_spmac_grid 4x4 == golden.sparse_matmul on 40 random 2:4 matmuls", "pass"),
        ],
    },
    {
        "key": "imentetcore", "num": "03", "name": "ImentetCore", "deity": "Imentet (welcome)",
        "domain": "Transformer attention unit", "doc": "docs/03_ImentetCore_Attention.md",
        "depends": ["ptahconv", "gebcore"], "phase": DONE4,
        "scope": "Phase 0/1 implements scaled dot-product attention with numerically-stable "
                 "softmax golden and a flash-style tiled pymodel. Phase 4: imentet_qk_score and "
                 "imentet_mask_add signed off on ASAP7 7nm.",
        "checkpoints": [
            ("I.1", "Golden: scaled dot-product attention", 0, "done"),
            ("I.2", "Golden: stable softmax", 0, "done"),
            ("I.3", "pymodel: flash-tiled attention", 1, "done"),
            ("I.4", "RTL: softmax (LUT exp + Newton)", 2, "done"),
            ("I.4b", "RTL: attention datapath integration", 2, "done"),
            ("I.5", "P&R: GDSII", 4, "done"),
            ("I.6", "Signoff: formal proof of attention-mask semantics — visible(m=0)=>score kept, masked(m=-inf)=>-inf (yosys-smtbmc+z3, all scores)", 5, "partial"),
        ],
        "tests": [
            ("test_attention_vs_reference", "attention == numpy reference", "pass"),
            ("test_softmax_stable", "softmax(x) == softmax(x+c), no overflow", "pass"),
            ("test_flash_equals_golden", "tiled flash attention == golden", "pass"),
            ("test_causal_mask", "causal mask zeroes future positions", "pass"),
            ("rtl: test_core (cocotb)", "imentet_core == golden.attention on 10 random blocks", "pass"),
        ],
    },
    {
        "key": "neithcore", "num": "07", "name": "NeithCore", "deity": "Neith (war/wisdom)",
        "domain": "Kyber-round-1-style lattice/NTT engine (Q=7681)", "doc": "docs/07_NeithCore_MLKEM.md",
        "depends": [],
        "phase": DONE4,
        "scope": "Phase 0/1: negacyclic NTT over Z_q (q=7681, NTT-friendly) plus a "
                 "Kyber-512-style module-LWE KEM that is self-consistent (decaps recovers the "
                 "encaps shared secret). Phase 2 IN PROGRESS: neith_modmul (Barrett mult "
                 "mod 7681) and neith_butterfly (Cooley-Tukey butterfly) RTL, both "
                 "cocotb-verified bit-exact vs the golden, PLUS neith_ntt — a multicycle "
                 "256-point in-place radix-2 NTT engine doing BOTH forward and inverse, "
                 "CYCLIC and full NEGACYCLIC (bit-reversed load, 8 stages x 128 butterflies, "
                 "fwd/inv twiddle ROMs + modmul w-update, inverse 1/N scale pass; `nega` adds "
                 "the psi=62 twist — forward pre-multiplies coeff i by psi^i on load, inverse "
                 "folds psi^-i into the scale pass, both via a running product so no 256-entry "
                 "ROM). Bit-exact vs golden.ntt_cyclic (both roots), golden.ntt/golden.intt, "
                 "forward->inverse roundtrips, AND an end-to-end HW negacyclic poly-mul that "
                 "matches schoolbook mod x^256+1. Phase 3: generic Yosys synth 0 latches "
                 "(modmul ~1.4K, butterfly ~1.65K, ntt ~59K cells / ~3.4K FFs). FIPS-203 exact "
                 "params (q=3329). Phase 4: neith_ntt, neith_butterfly, neith_polyaddsub, neith_modmul, neith_pointwise, and neith_compress signed off on ASAP7 7nm. NOTE: reference model, not "
                 "FIPS-203 certified.",
        "checkpoints": [
            ("N.1", "Golden: NTT mod 7681 + inverse (roundtrip)", 0, "done"),
            ("N.2", "Golden: NTT polymult == schoolbook", 0, "done"),
            ("N.3", "Golden: KEM keygen/encaps/decaps (self-consistent)", 0, "done"),
            ("N.4", "pymodel: NTT butterfly stages", 1, "done"),
            ("N.5", "RTL: modular multiplier (Barrett) + cocotb vs golden", 2, "done"),
            ("N.6", "RTL: Cooley-Tukey butterfly + cocotb vs golden", 2, "done"),
            ("N.7", "RTL: 256-pt NTT engine, forward + inverse (+1/N scale) + cocotb", 2, "done"),
            ("N.8", "RTL: psi pre/post-multiply for full negacyclic ntt()/intt()", 2, "done"),
            ("N.9", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("N.10", "Synthesis: ASAP7 liberty tech-mapping + SRAM macro (subsumed by P&R)", 3, "done"),
            ("N.11", "P&R: GDSII", 4, "done"),
            ("N.12", "Signoff: formal proof of Barrett modmul range r<Q — always a valid reduced field element (yosys-smtbmc+z3, all a,b<Q)", 5, "partial"),
            ("N.13", "Signoff: formal control-safety of the 256-pt NTT FSM — no illegal state + inverse-only scale pass (temporal k-induction, mutation-tested)", 5, "partial"),
        ],
        "tests": [
            ("test_ntt_roundtrip", "intt(ntt(p)) == p", "pass"),
            ("test_ntt_polymult", "NTT product == negacyclic schoolbook", "pass"),
            ("test_kem_correctness", "decaps(encaps) == shared secret over many trials", "pass"),
            ("test_pymodel_ntt", "staged butterfly == golden NTT", "pass"),
            ("rtl: test_modmul (cocotb)", "neith_modmul == (a*b)%7681 on 31K+ vectors", "pass"),
            ("rtl: test_butterfly (cocotb)", "neith_butterfly == golden CT butterfly on 32K+", "pass"),
            ("rtl: test_ntt (cocotb)", "neith_ntt cyclic+negacyclic fwd+inv == golden, roundtrips + HW poly-mul == schoolbook mod x^256+1", "pass"),
        ],
    },
    {
        "key": "sobekcore", "num": "08", "name": "SobekCore", "deity": "Sobek (Nile)",
        "domain": "Ray-triangle intersector", "doc": "docs/08_SobekCore_RayTrace.md",
        "depends": [], "phase": DONE4,
        "scope": "Phase 0/1 implements watertight Moller-Trumbore ray-triangle intersection "
                 "golden and a pipelined pymodel. Phase 4: sobek_dot3, sobek_lerp, sobek_ray_point, sobek_faceforward, sobek_cross, sobek_scale, and sobek_distance "
                 "signed off on ASAP7 7nm (registered boundary).",
        "checkpoints": [
            ("SB.1", "Golden: Moller-Trumbore intersection", 0, "done"),
            ("SB.2", "pymodel: pipelined intersector", 1, "done"),
            ("SB.3", "RTL: intersection datapath", 2, "done"),
            ("SB.4", "P&R: GDSII", 4, "done"),
            ("SB.6", "RTL: distance primitive", 2, "done"),
            ("SB.5", "Signoff: formal proof of sobek_scale multiply-commutativity s*v==v*s all 3 lanes (yosys-smtbmc+z3, all fp32)", 5, "partial"),
        ],
        "tests": [
            ("test_hit_center", "ray through triangle centroid hits, t correct", "pass"),
            ("test_miss", "ray outside triangle misses", "pass"),
            ("test_parallel", "ray parallel to triangle plane -> no hit", "pass"),
            ("test_barycentric", "u,v,w in [0,1] and sum to 1 on hit", "pass"),
            ("test_pymodel_equals_golden", "pipeline == golden", "pass"),
        ],
    },
    {
        "key": "atumcore", "num": "10", "name": "AtumCore", "deity": "Atum (creator)",
        "domain": "RISC-V Vector (RVV) unit", "doc": "docs/10_AtumCore_RVV.md",
        "depends": ["sethcore", "hapicore"], "phase": DONE4,
        "scope": "Phase 0/1 implements an RVV-subset golden (vsetvl, vadd/vsub/vmul/vmacc, "
                 "logic/shift, masked ops, vfadd/vfmul, vredsum) and an 8-lane pymodel. Phase 2 "
                 "IN PROGRESS: atum_valu.sv — a VLMAX(=8)-lane combinational vector integer ALU "
                 "(add/sub/mul/and/or/xor/sll/srl + vmacc vd+=vs1*vs2) with full RVV active-element semantics: a lane "
                 "writes only when body-active (i<vl) AND mask-active, else the destination element "
                 "is undisturbed; operands packed little-endian by lane. Bit-exact vs the golden "
                 "VectorUnit on directed corners + 6000 random ops (all ops/VL/mask). Phase 3: "
                 "atum_valu full-synth 0 latches (~33K cells, eight 32-bit multipliers; CI uses a "
                 "coarse 0-latch check, committed .stat is the full gate-level evidence). atum_vfpu.sv "
                 "— the fp32 vector lane (vfadd/vfmul) composing the bit-exact HapiCore fp32 cores "
                 "(hapi_fp32_add/mul) per lane with the same active-element write; bit-exact vs golden "
                 "on fp corners (zeros/inf/nan/subnormal/overflow) + 5000 random; 0-latch (CI coarse). "
                 "atum_vredu.sv — the vector reduction unit (vredsum = 32-bit wrapping sum, vredmax) "
                 "over active lanes (i<vl AND mask), scalar result; note the golden widens uint32->int64 "
                 "so vredmax is an UNSIGNED max (identity 0) — matched bit-for-bit. Bit-exact vs golden "
                 "on directed + 6000 random vredsum+vredmax; full-synth 0 latches (~3.1K cells). "
                 "atum_vexec.sv — the integrated vector execute unit: decodes a vclass (0=ALU->atum_valu, "
                 "1=FP->atum_vfpu, 2=RED->atum_vredu) + subop and muxes to one uniform vector output "
                 "(a reduction scalar lands in element 0, the rest keep vd_old). AtumCore's integration "
                 "capstone (like seth_core for SethCore). Bit-exact vs golden on directed + 6000 random "
                 "MIXED ops (int incl vmacc / fp vfadd-vfmul / vredsum-vredmax); 0-latch (CI coarse). "
                 "atum_vregfile.sv — NREGS x VLEN vector register file (2 async read + 1 sync write, "
                 "sync reset, no hardwired-zero since RVV v0 is a mask reg) verified on 4000 rw cycles; "
                 "atum_vsetvl.sv — VL = min(AVL, VLMAX) combinational, vs golden on edges + 2000 random. "
                 "Both full-synth 0 latches (vregfile ~40.8K cells DFF-heavy, vsetvl ~32). atum_vcore.sv "
                 "— a SINGLE-CYCLE VECTOR CORE (AtumCore's seth_core equivalent): fetch a 32-bit micro-op "
                 "(VSETVL/VOP/VHALT; vd/vs1/vs2/vclass/subop/avl fields) -> 3-port vregfile read -> "
                 "atum_vexec -> writeback, one op/cycle, VL gates the body, mask all-ones. TB preloads "
                 "imem + initial vregs, runs to HALT, compares the whole vector regfile to a golden runner "
                 "executing the same micro-program on VectorUnit. Bit-exact on a directed program "
                 "(int axpy/dot + fp vfmul/vfadd + vredsum/vredmax + partial-vl) + 40 random programs; "
                 "0-latch (CI coarse). The core gained a word-addressable VECTOR DATA MEMORY with "
                 "unit-stride VLD/VST micro-ops (3-bit opcode; VLD overwrites vd from dmem[base+i] for "
                 "i<vl else 0, VST writes vs1 lanes to dmem[base+i]); it now runs a real STRIP-MINED "
                 "integer axpy (vsetvl + VLD/VMACC/VST over a length-20 array) and the TB checks the "
                 "whole machine state (vregfile + data memory) vs the golden runner on the axpy + 40 "
                 "random load/store/op/reduction programs. AtumCore is a complete working vector processor. "
                 "Phase 4: atum_valu, atum_vredu, atum_vsadd, atum_vcompress, atum_viota, atum_vmask, atum_vsetvl, atum_vfpu, atum_vregfile, and atum_vimac signed off on ASAP7 7nm (registered boundaries).",
        "checkpoints": [
            ("AT.1", "Golden: RVV subset + vsetvl semantics", 0, "done"),
            ("AT.2", "Golden: masked ops + reductions", 0, "done"),
            ("AT.3", "pymodel: 8 ALU lanes", 1, "done"),
            ("AT.4", "pymodel: strip-mined axpy", 1, "done"),
            ("AT.6", "RTL: vector integer ALU lane array (atum_valu, incl vmacc) + cocotb vs golden", 2, "done"),
            ("AT.8", "RTL: fp32 vector lane (atum_vfpu, vfadd/vfmul over HapiCore fp32) + cocotb", 2, "done"),
            ("AT.9", "RTL: vector reduction unit (atum_vredu, vredsum/vredmax) + cocotb", 2, "done"),
            ("AT.10", "RTL: integrated vector execute unit (atum_vexec) + cocotb vs golden", 2, "done"),
            ("AT.11", "RTL: vector register file (atum_vregfile) + vsetvl (atum_vsetvl) + cocotb", 2, "done"),
            ("AT.12", "RTL: single-cycle vector core (atum_vcore) + vector memory (VLD/VST) running strip-mined programs", 2, "done"),
            ("AT.13", "P&R: GDSII at 500 MHz", 4, "done"),
            ("AT.14", "Signoff: formal proof of atum_valu lane algebra (yosys-smtbmc+z3, exhaustive)", 5, "partial"),
            ("AT.15", "Signoff: formal control-safety of atum_vcore — vl<=VLMAX (RVV lane/mem bound) + halt-sticky (temporal k-induction, datapath blackboxed, mutation-tested)", 5, "partial"),
        ],
        "tests": [
            ("test_vadd_vmul", "integer vector ops == numpy", "pass"),
            ("test_vmacc", "fused multiply-accumulate == numpy", "pass"),
            ("test_masked", "masked vadd only updates active lanes", "pass"),
            ("test_vredsum", "reduction == numpy sum", "pass"),
            ("test_vfmul_fp", "fp32 vector mul == numpy", "pass"),
            ("test_axpy_stripmined", "strip-mined axpy == a*x+y", "pass"),
            ("rtl: test_valu (cocotb)", "atum_valu.sv (add/sub/mul/logic/shift + vmacc) == golden on corners + 6000 random (all ops/vl/mask)", "pass"),
            ("rtl: test_vfpu (cocotb)", "atum_vfpu.sv (fp32 vfadd/vfmul) == golden on fp corners + 5000 random", "pass"),
            ("rtl: test_vredu (cocotb)", "atum_vredu.sv (vredsum/vredmax) == golden on directed + 6000 random", "pass"),
            ("rtl: test_vexec (cocotb)", "atum_vexec.sv integrated unit == golden on directed + 6000 random mixed ALU/FP/RED ops", "pass"),
            ("rtl: test_vregfile (cocotb)", "atum_vregfile.sv == model on 4000 rw cycles + reset", "pass"),
            ("rtl: test_vsetvl (cocotb)", "atum_vsetvl.sv VL=min(avl,VLMAX) == golden on edges + 2000 random", "pass"),
            ("rtl: test_vcore (cocotb)", "atum_vcore.sv final vregfile + data memory == golden runner on strip-mined axpy + 40 random load/store/op programs", "pass"),
        ],
    },
    {
        "key": "racore", "num": "00", "name": "RaCore", "deity": "Ra (supreme creator)",
        "domain": "Heterogeneous AI SoC (capstone)", "doc": "docs/00_RaCore_SoC.md",
        "depends": ["sethcore", "atumcore", "hapicore", "anubiscore", "bastcore",
                    "ptahconv", "gebcore", "imentetcore", "neithcore", "sobekcore"],
        "phase": _ph("done", "done", "partial", "partial", "partial", "partial"),
        "scope": "Phase 0/1 implements the KAI register/DMA contract model, a NoC + "
                 "descriptor-DMA functional model, a KAI conformance harness, and an "
                 "end-to-end axpy that drives a KAI accelerator through the fabric. "
                 "Phase 4: ra_noc_arbiter and ra_kai_regs signed off on ASAP7 7nm.",
        "checkpoints": [
            ("RA.1", "Golden: KAI register model + conformance harness", 0, "done"),
            ("RA.2", "Golden: NoC crossbar + descriptor DMA", 0, "done"),
            ("RA.3", "Golden: end-to-end axpy over KAI", 0, "done"),
            ("RA.4", "pymodel: arbitration + DMA timing", 1, "done"),
            ("RA.5", "RTL: NoC + DMA", 2, "done"),
            ("RA.7", "RTL: RaCore-Lite top integration", 2, "done"),
            ("RA.10", "P&R: Lite hierarchical GDSII", 4, "done"),
            ("RA.11", "Signoff: formal proof of NoC arbiter grant safety (k-induction, yosys-smtbmc+z3)", 5, "partial"),
            ("RA.11", "Flagship demo: CNN inference + attestation", 5, "todo"),
        ],
        "tests": [
            ("test_kai_conformance", "mock accel exposes mandatory KAI registers", "pass"),
            ("test_dma_2d", "2D/strided DMA copies correct bytes", "pass"),
            ("test_noc_arbitration", "two masters share the crossbar fairly", "pass"),
            ("test_axpy_end2end", "host->DMA->accel->host axpy == a*x+y", "pass"),
        ],
    },
]

# Standard 6-phase build steps every project follows (rendered into STEPS.md,
# annotated per-project with phase status).
STD_STEPS = [
    (0, "Write the numpy/pure-python golden reference (the mathematical truth)"),
    (0, "Write golden tests vs known-correct software; achieve passing pytest"),
    (1, "Write the cycle/lane/round pymodel; assert it equals the golden bit-for-bit"),
    (2, "Write SystemVerilog RTL + cocotb testbench (Verilator); coverage >= 90%"),
    (3, "Yosys synthesis: 0 latches, gate count <= target"),
    (4, "OpenROAD P&R on ASAP7: DRC clean, timing closed at target Fmax -> GDSII"),
    (5, "CI pipeline + docs finalization; `make all` green"),
]


def by_key(key):
    for p in PROJECTS:
        if p["key"] == key:
            return p
    raise KeyError(key)
