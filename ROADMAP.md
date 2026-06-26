# 𓂀 KemetCore — Master Roadmap

> *"A journey of a thousand gates begins with a single flip-flop."*
>
> This roadmap defines the phased execution plan for all 10 KemetCore projects. Each project progresses through 6 phases (0–5), with concrete checkpoints, acceptance criteria, and estimated test counts. Projects are ordered for maximum skill/knowledge transfer — earlier projects build the tooling and expertise that later ones depend on.

---

## Phase Definitions

Every project follows the same 6-phase lifecycle:

| Phase | Name | Deliverable | Exit Criteria |
|:-----:|------|-------------|---------------|
| **0** | Spec & Golden | Architecture document + golden reference (numpy) | All math verified against known-correct software |
| **1** | pymodel | Cycle-level Python behavioral model | pymodel passes all tests; tests reviewed |
| **2** | RTL | SystemVerilog implementation + cocotb tests | All RTL tests pass; coverage ≥90% |
| **3** | Synthesis | Yosys elaboration + gate-level netlist | 0 latches; ≤target gate count |
| **4** | P&R | OpenROAD floorplan → GDSII | DRC clean; timing closed at target Fmax |
| **5** | Signoff | CI pipeline + documentation finalization | `make all` passes; docs complete |

---

## Execution Order & Dependencies

```
Phase 1 — Foundation (build the tooling)
  09. HapiCore ← no dependencies, pure arithmetic, creates FPU library
  06. AnubisCore ← no dependencies, pure crypto, creates hash library

Phase 2 — Compute Primitives (leverage FPU library)
  05. BastCore ← depends on HapiCore (BF16 multiply)
  01. SethCore ← depends on HapiCore (FPU for M extension)

Phase 3 — ML Accelerators (build on PtahCore patterns)
  02. PtahConv ← depends on BastCore (BF16 datapath)
  04. GebCore ← depends on BastCore (sparse BF16 matmul)
  03. ImentetCore ← depends on PtahConv + GebCore

Phase 4 — Advanced (graphics + post-quantum + vector)
  08. SobekCore ← independent, uses HapiCore
  07. NeithCore ← independent, standalone arithmetic
  10. AtumCore ← depends on SethCore (adds vector to scalar core)
```

---

## Project Status Overview

| # | Project | Phase | Status | Est. Tests | Est. RTL Modules | Est. Gates |
|:-:|---------|:-----:|:------:|:----------:|:-----------------:|:----------:|
| 09 | [HapiCore](docs/09_HapiCore_FPU.md) | 0 | 📋 Planning | 60 | 8 | 30K |
| 06 | [AnubisCore](docs/06_AnubisCore_HashEngine.md) | 0 | 📋 Planning | 25 | 6 | 15K |
| 05 | [BastCore](docs/05_BastCore_BF16Tensor.md) | 0 | 📋 Planning | 35 | 10 | 4M |
| 01 | [SethCore](docs/01_SethCore_RV32IM_CPU.md) | 0 | 📋 Planning | 80 | 25 | 50K |
| 02 | [PtahConv](docs/02_PtahConv_Convolution.md) | 0 | 📋 Planning | 40 | 12 | 6M |
| 04 | [GebCore](docs/04_GebCore_SparseMatmul.md) | 0 | 📋 Planning | 30 | 8 | 4M |
| 03 | [ImentetCore](docs/03_ImentetCore_Attention.md) | 0 | 📋 Planning | 35 | 10 | 3M |
| 08 | [SobekCore](docs/08_SobekCore_RayTrace.md) | 0 | 📋 Planning | 35 | 8 | 30K |
| 07 | [NeithCore](docs/07_NeithCore_MLKEM.md) | 0 | 📋 Planning | 50 | 15 | 100K |
| 10 | [AtumCore](docs/10_AtumCore_RVV.md) | 0 | 📋 Planning | 100+ | 20+ | 100K+ |

**Legend:** 📋 Planning | 🔧 In Progress | ✅ Complete

---

## Detailed Phase Roadmap

### Phase 0 — All Projects (Current)

All 10 projects are currently in Phase 0 (Spec & Golden). The deliverables are the documents in this repository.

| Checkpoint | Criteria | Verification |
|------------|----------|-------------|
| PO.1 | Architecture document written | Reviewed and merged |
| PO.2 | Golden reference implemented in numpy | Tested against known-correct output |
| PO.3 | Golden reference tests written | pytest passes with coverage ≥95% |
| PO.4 | Test plan documented | Covers directed + random + edge cases |
| PO.5 | Risk register documented | Known challenges listed with mitigations |
| PO.6 | Estimated gate count and area | Based on comparable designs |

---

### Phase 1 — First Wave (Projects 09, 06)

These are the smallest, most self-contained projects. They build the infrastructure (FPU library, hash library) that everything else depends on.

#### HapiCore (Project 09)

| Checkpoint | Description | Est. Effort |
|------------|-------------|:-----------:|
| H1.1 | FP16 golden ref (numpy): add, mul, FMA | 2 days |
| H1.2 | BF16 golden ref: add, mul, FMA | 1 day |
| H1.3 | FP32 golden ref: div, sqrt | 2 days |
| H1.4 | FP64 golden ref: add, mul, FMA, div, sqrt | 3 days |
| H1.5 | IEEE-754 edge case test suite | 2 days |
| H1.6 | pymodel: cycle-level FPU pipeline | 3 days |
| H1.7 | RTL: parameterized FP16/BF16 add + mul | 4 days |
| H1.8 | RTL: FP32 div + sqrt (Goldschmidt) | 5 days |
| H1.9 | RTL: FP64 multi-cycle | 5 days |
| H1.10 | cocotb tests: exhaustive FP16 + random wider | 3 days |
| H1.11 | Synthesis: Yosys elaboration | 1 day |
| H1.12 | P&R: smallest macro (FP16 mul) | 3 days |

#### AnubisCore (Project 06)

| Checkpoint | Description | Est. Effort |
|------------|-------------|:-----------:|
| A1.1 | SHA-256 golden ref (numpy via hashlib) | 1 day |
| A1.2 | SHA-3 (Keccak-f[1600]) golden ref | 2 days |
| A1.3 | NIST test vector harness | 1 day |
| A1.4 | pymodel: SHA-256 message schedule + compression | 2 days |
| A1.5 | pymodel: Keccak-f[1600] state engine | 2 days |
| A1.6 | RTL: SHA-256 datapath (64 rounds) | 3 days |
| A1.7 | RTL: Keccak-f[1600] (24 rounds) | 3 days |
| A1.8 | RTL: shared message scheduler + padding | 2 days |
| A1.9 | cocotb: all NIST vectors + random | 2 days |
| A1.10 | Synthesis + P&R | 2 days |

---

### Phase 2 — Second Wave (Projects 05, 01)

#### BastCore (Project 05)

| Checkpoint | Description | Est. Effort |
|------------|-------------|:-----------:|
| B2.1 | BF16 golden ref: matmul (using HapiCore) | 1 day |
| B2.2 | pymodel: BF16 MAC array (adapted from PtahCore) | 2 days |
| B2.3 | RTL: BF16 decode + encode | 2 days |
| B2.4 | RTL: BF16 mul + FP32 add (from HapiCore) | 2 days |
| B2.5 | RTL: mac_cell for BF16 | 2 days |
| B2.6 | RTL: mac_grid 16×16 adaptation | 2 days |
| B2.7 | cocotb: point tests + random matmul | 3 days |
| B2.8 | Synthesis: compare area to PtahCore | 1 day |
| B2.9 | P&R: full array | 3 days |

#### SethCore (Project 01)

| Checkpoint | Description | Est. Effort |
|------------|-------------|:-----------:|
| S2.1 | RV32I golden ref: Spike-compatible ISA sim | 4 days |
| S2.2 | RISC-V test vector suite (riscv-tests) | 1 day |
| S2.3 | pymodel: 5-stage pipeline | 3 days |
| S2.4 | pymodel: hazard detection + forwarding | 2 days |
| S2.5 | RTL: fetch stage + branch predictor | 3 days |
| S2.6 | RTL: decode stage + register file | 2 days |
| S2.7 | RTL: execute stage + ALU (from HapiCore for M) | 4 days |
| S2.8 | RTL: memory stage + data cache interface | 2 days |
| S2.9 | RTL: writeback stage + forwarding muxes | 2 days |
| S2.10 | RTL: CSR + control flow | 2 days |
| S2.11 | cocotb: each instruction → Spike comparison | 5 days |
| S2.12 | cocotb: pipeline hazard stress tests | 3 days |
| S2.13 | Synthesis: ~50K gates target | 2 days |
| S2.14 | P&R: core macro | 4 days |

---

### Phase 3 — Third Wave (Projects 02, 04, 03)

These build on PtahCore + BastCore to create a complete ML inference pipeline.

| # | Project | Key Challenge | Est. Effort |
|:-:|---------|---------------|:-----------:|
| 02 | PtahConv | Dataflow: converting conv loops to systolic array | 30 days |
| 04 | GebCore | Sparsity metadata handling + variable-length datapath | 25 days |
| 03 | ImentetCore | Softmax in hardware (division/exponentiation) | 25 days |

---

### Phase 4 — Fourth Wave (Projects 08, 07, 10)

| # | Project | Key Challenge | Est. Effort |
|:-:|---------|---------------|:-----------:|
| 08 | SobekCore | BVH stack management + watertight intersection | 25 days |
| 07 | NeithCore | NTT datapath + modular arithmetic at speed | 35 days |
| 10 | AtumCore | Vector register file + masked execution + RVV spec complexity | 45 days |

---

## Milestone Timeline

```
    Project       │ Phase 0  Phase 1  Phase 2  Phase 3  Phase 4  Phase 5
──────────────────┼──────────────────────────────────────────────────────
09. HapiCore      │ ■■■■    ■■■■■■   ■■■■■■   ■■■■■    ■■■■     ■■■
06. AnubisCore    │ ■■■      ■■■■■    ■■■■■    ■■■■     ■■■      ■■
05. BastCore      │ ■■■■     ■■■■■■   ■■■■■■   ■■■■■    ■■■■     ■■■
01. SethCore      │ ■■■■■    ■■■■■■■  ■■■■■■■  ■■■■■    ■■■■■    ■■■■
02. PtahConv      │ ■■■■     ■■■■■■   ■■■■■■   ■■■■■    ■■■■     ■■■
04. GebCore       │ ■■■■     ■■■■■■   ■■■■■■   ■■■■■    ■■■■     ■■■
03. ImentetCore   │ ■■■■     ■■■■■■   ■■■■■■   ■■■■■    ■■■■     ■■■
08. SobekCore     │ ■■■■     ■■■■■    ■■■■■    ■■■■     ■■■      ■■
07. NeithCore     │ ■■■■■    ■■■■■■■  ■■■■■■■  ■■■■■    ■■■■■    ■■■■
10. AtumCore      │ ■■■■■    ■■■■■■■  ■■■■■■■  ■■■■■    ■■■■■    ■■■■■
```
*Each ■ ≈ 20% of the phase. Actual durations depend on complexity.*

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Verilator doesn't support some SV constructs | Medium | High | Test early on a small module; fall back to commercial sim for that module |
| ASAP7 PDK timing is overly optimistic | Medium | Medium | Use pessimistic wire load models; target +20% frequency margin |
| RVV spec is enormous (400+ pages) | High | Medium | Implement a subset first (VLEN=128, ELEN=32, LMUL=1); extend later |
| Softmax hardware division is expensive | Medium | Medium | Use LUT-based approximation + Newton iteration; verify error bounds |
| NTT butterfly has high routing congestion | Medium | High | Floorplan early; use H-tree for data distribution |
| BVH traversal has unpredictable latency | High | Medium | Implement as a pipelined state machine with stall output |
| Sparse matmul throughput gain is less than expected | Medium | Medium | Benchmark on real model weights before committing to P&R |
| Single developer, projects take time | High | Medium | Prioritize by dependency graph; each project is independently shippable |

---

## CI Pipeline (Goal State)

```yaml
# .github/workflows/ci.yml — unified CI for all projects
name: kemet-core-ci
on: [push, pull_request]

jobs:
  golden-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [hapi, anubis, bast, seth, ptahconv, geb, imentet, sobek, neith, atum]
    steps:
      - uses: actions/checkout@v4
      - run: pip install numpy pytest
      - run: cd projects/${{ matrix.project }}/golden && python -m pytest -v

  pymodel-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install numpy pytest
      - run: for d in projects/*/pymodel; do cd $d && python -m pytest -v; done

  rtl-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt install verilator
      - run: pip install cocotb pytest
      - run: for d in projects/*/rtl/tb; do cd $d && make; done

  synthesis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt install yosys
      - run: for d in projects/*/synth; do cd $d && yosys -s area.ys; done
```

---

## How to Contribute / Track Progress

Each project's detailed spec lives in `docs/XX_Name.md`. Each spec contains:

1. **Technical Overview** — What it does and why it matters
2. **Architecture** — Block diagrams and module hierarchy
3. **Specification Tables** — Interfaces, parameters, timing
4. **Golden Reference** — The mathematical model
5. **Testing Strategy** — What gets tested and how
6. **Checkpoints** — Same as above but with specific files/modules
7. **Comparison with Prior Art** — What's new/different
8. **Risk Register** — Project-specific risks

---

## Project Repositories

Each project will eventually live in its own repository under the Lord1Egypt GitHub organization. This repository serves as the meta-architecture and roadmap.

| Project | Status | Repository |
|---------|--------|------------|
| PtahCore | ✅ Complete | [Lord1Egypt/PtahCore](https://github.com/Lord1Egypt/PtahCore) |
| 09 HapiCore | 📋 Planning | _not yet created_ |
| 06 AnubisCore | 📋 Planning | _not yet created_ |
| 05 BastCore | 📋 Planning | _not yet created_ |
| 01 SethCore | 📋 Planning | _not yet created_ |
| 02 PtahConv | 📋 Planning | _not yet created_ |
| 04 GebCore | 📋 Planning | _not yet created_ |
| 03 ImentetCore | 📋 Planning | _not yet created_ |
| 08 SobekCore | 📋 Planning | _not yet created_ |
| 07 NeithCore | 📋 Planning | _not yet created_ |
| 10 AtumCore | 📋 Planning | _not yet created_ |
