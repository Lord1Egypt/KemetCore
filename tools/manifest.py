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


# Every project currently has Phase 0 (golden) + Phase 1 (pymodel) implemented and
# tested in Python; Phases 2-5 (RTL -> GDSII) are not started (the RAM-heavy part).
P01 = _ph("done", "done", "todo", "todo", "todo", "todo")

PROJECTS = [
    {
        "key": "hapicore", "num": "09", "name": "HapiCore", "deity": "Hapi (Nile flood)",
        "domain": "IEEE-754 FPU library", "doc": "docs/09_HapiCore_FPU.md",
        "depends": [],
        "phase": _ph("done", "done", "partial", "partial", "todo", "todo"),
        "scope": "Phase 0/1: fp16/bf16/fp32 add, mul, fma, cmp, classify with correct "
                 "bf16 round-to-nearest-even. Phase 2 IN PROGRESS: bf16 AND fp32 multiplier "
                 "+ adder RTL (hapi_bf16_mul/add, hapi_fp32_mul/add), each cocotb-verified "
                 "bit-exact vs the golden/numpy (subnormals in+out, RNE, Inf/NaN/signed-zero, "
                 "cancellation). Phase 3: generic Yosys synth 0 latches (bf16 mul ~873/add "
                 "~650; fp32 mul ~5046/add ~1792 cells). fp32 add unblocks the BastCore "
                 "tensor-core accumulate. fp16 datapath, div/sqrt, ASAP7 + P&R (Phase 4) pending.",
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
            ("HA.12", "RTL: fp16 add+mul + fp_div (Goldschmidt) + fma", 2, "todo"),
            ("HA.13", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("HA.14", "Synthesis: ASAP7 liberty tech-mapping", 3, "todo"),
            ("HA.15", "P&R: bf16/fp32 add+mul GDSII", 4, "todo"),
        ],
        "tests": [
            ("test_add_matches_numpy", "fp16/fp32 add == numpy IEEE result", "pass"),
            ("test_bf16_round_cases", "hand-computed bf16 RNE cases", "pass"),
            ("test_mul_commutative", "a*b == b*a across formats", "pass"),
            ("test_fma_more_accurate", "fma beats separate mul+add on a known case", "pass"),
            ("test_specials", "NaN/Inf propagation + signed zero", "pass"),
            ("test_pymodel_latency", "pipeline reports correct cycle latency", "pass"),
            ("rtl: test_bf16_mul (cocotb)", "hapi_bf16_mul == golden on 7K+ products", "pass"),
            ("rtl: test_bf16_add (cocotb)", "hapi_bf16_add == golden on 12K+ sums", "pass"),
            ("rtl: test_fp32_mul (cocotb)", "hapi_fp32_mul == numpy fp32 on 40K+ products", "pass"),
            ("rtl: test_fp32_add (cocotb)", "hapi_fp32_add == numpy fp32 on 70K+ sums", "pass"),
        ],
    },
    {
        "key": "anubiscore", "num": "06", "name": "AnubisCore", "deity": "Anubis (embalming)",
        "domain": "SHA-256 / SHA-3 hash engine", "doc": "docs/06_AnubisCore_HashEngine.md",
        "depends": [],
        "phase": _ph("done", "done", "done", "partial", "todo", "todo"),
        "scope": "Phase 0/1: full SHA-256 + Keccak/SHA3-256 in pure Python vs hashlib. "
                 "Phase 2 DONE: SHA-256 + SHA3-256/Keccak RTL, each verified bit-exact in "
                 "cocotb/Verilator 5.020. Phase 3 IN PROGRESS: generic Yosys synth passes "
                 "with 0 latches (sha256 ~6.4K cells, sha3 ~15.8K cells); ASAP7 liberty "
                 "tech-mapping + OpenROAD P&R (Phase 4) pending (no PDK/OpenROAD locally).",
        "checkpoints": [
            ("A1.1", "Golden: SHA-256 vs hashlib", 0, "done"),
            ("A1.2", "Golden: Keccak-f[1600] / SHA3-256 vs hashlib", 0, "done"),
            ("A1.3", "Golden: NIST-style vectors (empty/abc/long)", 0, "done"),
            ("A1.4", "pymodel: SHA-256 round engine (64 rounds)", 1, "done"),
            ("A1.5", "pymodel: Keccak round engine (24 rounds)", 1, "done"),
            ("A1.6", "RTL: SHA-256 datapath + cocotb (Verilator)", 2, "done"),
            ("A1.7", "RTL: Keccak-f[1600] + cocotb (Verilator)", 2, "done"),
            ("A1.8", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("A1.9", "Synthesis: ASAP7 liberty tech-mapping", 3, "todo"),
            ("A1.10", "P&R: GDSII", 4, "todo"),
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
        "depends": ["hapicore"], "phase": P01,
        "scope": "Phase 0/1 implements bf16 matmul (bf16 inputs, fp32 accumulate) and a "
                 "16x16 systolic dataflow pymodel.",
        "checkpoints": [
            ("B2.1", "Golden: bf16 matmul (fp32 accumulate)", 0, "done"),
            ("B2.2", "pymodel: systolic MAC array", 1, "done"),
            ("B2.5", "RTL: mac_cell (bf16)", 2, "todo"),
            ("B2.6", "RTL: mac_grid 16x16", 2, "todo"),
            ("B2.9", "P&R: full array GDSII", 4, "todo"),
        ],
        "tests": [
            ("test_matmul_vs_numpy", "bf16 matmul within bf16 tolerance of fp32 ref", "pass"),
            ("test_identity", "A @ I == A (bf16 representable)", "pass"),
            ("test_pymodel_equals_golden", "systolic pymodel == golden matmul", "pass"),
        ],
    },
    {
        "key": "sethcore", "num": "01", "name": "SethCore", "deity": "Seth (strength)",
        "domain": "RV32IM pipelined CPU", "doc": "docs/01_SethCore_RV32IM_CPU.md",
        "depends": ["hapicore"],
        "phase": _ph("done", "done", "partial", "partial", "todo", "todo"),
        "scope": "Phase 0/1: RV32I+M ISA sim + 5-stage pymodel. Phase 2 IN PROGRESS: "
                 "seth_alu.sv (RV32 ALU) and seth_muldiv.sv (RV32M mul/div/rem) both "
                 "cocotb-verified bit-exact vs golden; fetch/decode/pipeline RTL pending. "
                 "Phase 3: ALU Yosys-synthesized 0 latches; combinational divider synth "
                 "deferred (needs a sequential/iterative divider — generic synth explodes).",
        "checkpoints": [
            ("S2.1", "Golden: RV32I ISA simulator", 0, "done"),
            ("S2.2", "Golden: M-extension (mul/div/rem)", 0, "done"),
            ("S2.3", "pymodel: 5-stage pipeline", 1, "done"),
            ("S2.4", "pymodel: hazard forwarding", 1, "done"),
            ("S2.7", "RTL: ALU (seth_alu) + cocotb vs golden", 2, "done"),
            ("S2.8", "RTL: mul/div (seth_muldiv) + cocotb vs golden", 2, "done"),
            ("S2.10", "RTL: fetch/decode/regfile/pipeline", 2, "todo"),
            ("S2.9", "Synthesis: ALU Yosys, 0 latches", 3, "done"),
            ("S2.11", "cocotb: per-instruction vs Spike", 2, "todo"),
            ("S2.14", "P&R: core macro", 4, "todo"),
        ],
        "tests": [
            ("test_arith_program", "sum-1..10 loop returns 55", "pass"),
            ("test_fibonacci", "fib(10) == 55", "pass"),
            ("test_mul_div", "mul/div/rem match Python semantics", "pass"),
            ("test_branches", "beq/bne/blt/bge taken correctly", "pass"),
            ("test_pymodel_equals_golden", "pipeline result == ISA sim", "pass"),
            ("rtl: test_alu (cocotb)", "seth_alu.sv == golden _alu_r on all ops", "pass"),
            ("rtl: test_muldiv (cocotb)", "seth_muldiv.sv == golden _muldiv (incl edges)", "pass"),
        ],
    },
    {
        "key": "ptahconv", "num": "02", "name": "PtahConv", "deity": "Ptah (craftsmen)",
        "domain": "Direct convolution accelerator", "doc": "docs/02_PtahConv_Convolution.md",
        "depends": ["bastcore"], "phase": P01,
        "scope": "Phase 0/1 implements conv2d (NCHW, stride/pad) via im2col+matmul golden and "
                 "a tiled dataflow pymodel.",
        "checkpoints": [
            ("PC.1", "Golden: conv2d (stride/pad) vs reference", 0, "done"),
            ("PC.2", "pymodel: tiled im2col dataflow", 1, "done"),
            ("PC.3", "RTL: systolic conv array", 2, "todo"),
            ("PC.4", "P&R: GDSII (tile-abutted)", 4, "todo"),
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
        "depends": ["bastcore"], "phase": P01,
        "scope": "Phase 0/1 implements 2:4 structured-sparse matmul (compress to 2-of-4 + "
                 "metadata) and a pymodel that skips pruned MACs, with a dense cross-check.",
        "checkpoints": [
            ("G.1", "Golden: 2:4 compress + sparse matmul", 0, "done"),
            ("G.2", "pymodel: metadata-driven MAC", 1, "done"),
            ("G.3", "RTL: sparse datapath", 2, "todo"),
            ("G.4", "P&R: GDSII", 4, "todo"),
        ],
        "tests": [
            ("test_sparse_equals_dense", "sparse matmul == dense matmul on 2:4 weights", "pass"),
            ("test_compression_metadata", "2-of-4 selection + indices correct", "pass"),
            ("test_macs_halved", "pymodel performs ~50% of dense MACs", "pass"),
        ],
    },
    {
        "key": "imentetcore", "num": "03", "name": "ImentetCore", "deity": "Imentet (welcome)",
        "domain": "Transformer attention unit", "doc": "docs/03_ImentetCore_Attention.md",
        "depends": ["ptahconv", "gebcore"], "phase": P01,
        "scope": "Phase 0/1 implements scaled dot-product attention with numerically-stable "
                 "softmax golden and a flash-style tiled pymodel.",
        "checkpoints": [
            ("I.1", "Golden: scaled dot-product attention", 0, "done"),
            ("I.2", "Golden: stable softmax", 0, "done"),
            ("I.3", "pymodel: flash-tiled attention", 1, "done"),
            ("I.4", "RTL: softmax (LUT exp + Newton)", 2, "todo"),
            ("I.5", "P&R: GDSII", 4, "todo"),
        ],
        "tests": [
            ("test_attention_vs_reference", "attention == numpy reference", "pass"),
            ("test_softmax_stable", "softmax(x) == softmax(x+c), no overflow", "pass"),
            ("test_flash_equals_golden", "tiled flash attention == golden", "pass"),
            ("test_causal_mask", "causal mask zeroes future positions", "pass"),
        ],
    },
    {
        "key": "neithcore", "num": "07", "name": "NeithCore", "deity": "Neith (war/wisdom)",
        "domain": "ML-KEM (Kyber) lattice KEM", "doc": "docs/07_NeithCore_MLKEM.md",
        "depends": [],
        "phase": _ph("done", "done", "partial", "partial", "todo", "todo"),
        "scope": "Phase 0/1: negacyclic NTT over Z_q (q=7681, NTT-friendly) plus a "
                 "Kyber-512-style module-LWE KEM that is self-consistent (decaps recovers the "
                 "encaps shared secret). Phase 2 IN PROGRESS: neith_modmul (Barrett mult "
                 "mod 7681) and neith_butterfly (Cooley-Tukey butterfly) RTL, both "
                 "cocotb-verified bit-exact vs the golden. Phase 3: generic Yosys synth 0 "
                 "latches (modmul ~1.4K, butterfly ~1.65K cells). Multicycle 256-pt NTT "
                 "engine + FIPS-203 exact params (q=3329, incomplete NTT) + ASAP7 pending. "
                 "NOTE: reference model, not FIPS-203 certified.",
        "checkpoints": [
            ("N.1", "Golden: NTT mod 7681 + inverse (roundtrip)", 0, "done"),
            ("N.2", "Golden: NTT polymult == schoolbook", 0, "done"),
            ("N.3", "Golden: KEM keygen/encaps/decaps (self-consistent)", 0, "done"),
            ("N.4", "pymodel: NTT butterfly stages", 1, "done"),
            ("N.5", "RTL: modular multiplier (Barrett) + cocotb vs golden", 2, "done"),
            ("N.6", "RTL: Cooley-Tukey butterfly + cocotb vs golden", 2, "done"),
            ("N.7", "RTL: multicycle 256-point NTT engine", 2, "todo"),
            ("N.8", "Synthesis: generic Yosys, 0 latches + gate count", 3, "done"),
            ("N.9", "Synthesis: ASAP7 liberty tech-mapping", 3, "todo"),
            ("N.10", "P&R: GDSII", 4, "todo"),
        ],
        "tests": [
            ("test_ntt_roundtrip", "intt(ntt(p)) == p", "pass"),
            ("test_ntt_polymult", "NTT product == negacyclic schoolbook", "pass"),
            ("test_kem_correctness", "decaps(encaps) == shared secret over many trials", "pass"),
            ("test_pymodel_ntt", "staged butterfly == golden NTT", "pass"),
            ("rtl: test_modmul (cocotb)", "neith_modmul == (a*b)%7681 on 31K+ vectors", "pass"),
            ("rtl: test_butterfly (cocotb)", "neith_butterfly == golden CT butterfly on 32K+", "pass"),
        ],
    },
    {
        "key": "sobekcore", "num": "08", "name": "SobekCore", "deity": "Sobek (Nile)",
        "domain": "Ray-triangle intersector", "doc": "docs/08_SobekCore_RayTrace.md",
        "depends": [], "phase": P01,
        "scope": "Phase 0/1 implements watertight Moller-Trumbore ray-triangle intersection "
                 "golden and a pipelined pymodel.",
        "checkpoints": [
            ("SB.1", "Golden: Moller-Trumbore intersection", 0, "done"),
            ("SB.2", "pymodel: pipelined intersector", 1, "done"),
            ("SB.3", "RTL: intersection datapath", 2, "todo"),
            ("SB.4", "P&R: GDSII", 4, "todo"),
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
        "depends": ["sethcore", "hapicore"], "phase": P01,
        "scope": "Phase 0/1 implements an RVV-subset golden (vsetvl, vadd/vsub/vmul/vmacc, "
                 "logic/shift, masked ops, vfadd/vfmul, vredsum) and an 8-lane pymodel.",
        "checkpoints": [
            ("AT.1", "Golden: RVV subset + vsetvl semantics", 0, "done"),
            ("AT.2", "Golden: masked ops + reductions", 0, "done"),
            ("AT.3", "pymodel: 8 ALU lanes", 1, "done"),
            ("AT.4", "pymodel: strip-mined axpy", 1, "done"),
            ("AT.6", "RTL: ALU lane group", 2, "todo"),
            ("AT.13", "P&R: GDSII at 500 MHz", 4, "todo"),
        ],
        "tests": [
            ("test_vadd_vmul", "integer vector ops == numpy", "pass"),
            ("test_vmacc", "fused multiply-accumulate == numpy", "pass"),
            ("test_masked", "masked vadd only updates active lanes", "pass"),
            ("test_vredsum", "reduction == numpy sum", "pass"),
            ("test_vfmul_fp", "fp32 vector mul == numpy", "pass"),
            ("test_axpy_stripmined", "strip-mined axpy == a*x+y", "pass"),
        ],
    },
    {
        "key": "racore", "num": "00", "name": "RaCore", "deity": "Ra (supreme creator)",
        "domain": "Heterogeneous AI SoC (capstone)", "doc": "docs/00_RaCore_SoC.md",
        "depends": ["sethcore", "atumcore", "hapicore", "anubiscore", "bastcore",
                    "ptahconv", "gebcore", "imentetcore", "neithcore", "sobekcore"],
        "phase": _ph("done", "done", "todo", "todo", "todo", "todo"),
        "scope": "Phase 0/1 implements the KAI register/DMA contract model, a NoC + "
                 "descriptor-DMA functional model, a KAI conformance harness, and an "
                 "end-to-end axpy that drives a KAI accelerator through the fabric.",
        "checkpoints": [
            ("RA.1", "Golden: KAI register model + conformance harness", 0, "done"),
            ("RA.2", "Golden: NoC crossbar + descriptor DMA", 0, "done"),
            ("RA.3", "Golden: end-to-end axpy over KAI", 0, "done"),
            ("RA.4", "pymodel: arbitration + DMA timing", 1, "done"),
            ("RA.5", "RTL: NoC + DMA", 2, "todo"),
            ("RA.7", "RTL: RaCore-Lite top integration", 2, "todo"),
            ("RA.10", "P&R: Lite hierarchical GDSII", 4, "todo"),
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
