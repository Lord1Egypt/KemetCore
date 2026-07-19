# 𓆎 KemetCore — Open-Source Silicon Laboratory

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Lord1Egypt/KemetCore)](https://github.com/Lord1Egypt/KemetCore/releases)
[![Stars](https://img.shields.io/github/stars/Lord1Egypt/KemetCore)](https://github.com/Lord1Egypt/KemetCore/stargazers)
[![CI](https://github.com/Lord1Egypt/KemetCore/actions/workflows/kemetcore-ci.yml/badge.svg)](https://github.com/Lord1Egypt/KemetCore/actions)
[![RTL](https://img.shields.io/badge/RTL-SystemVerilog-3480c0)](https://en.wikipedia.org/wiki/SystemVerilog)
[![Verification](https://img.shields.io/badge/Verification-cocotb-00c853)](https://docs.cocotb.org/)
[![Simulation](https://img.shields.io/badge/Simulation-Verilator-ff6d00)](https://verilator.org/)
[![Synthesis](https://img.shields.io/badge/Synthesis-Yosys-2196f3)](https://yosyshq.net/yosys/)
[![PDK](https://img.shields.io/badge/PDK-ASAP7%207nm-9c27b0)](https://github.com/The-OpenROAD-Project/asap7)
[![Status](https://img.shields.io/badge/Status-100%25%20Complete-brightgreen)](#)
[![Wiki](https://img.shields.io/badge/Wiki-21%20pages-9c27b0)](wiki/Home.md)

> **📚 [Browse the Wiki →](wiki/Home.md)** — Architecture, methodology, all 11 cores explained in stunning detail

> **From RTL to GDSII. Every project starts with a golden model, ends with silicon.**
>
> Named after **Kemet** (𓆎𓅓𓏏𓊖) — the ancient Egyptian name for Egypt, meaning "the black land" — this repository is a collection of open-source hardware accelerators spanning CPUs, ML accelerators, cryptographic engines, graphics hardware, and more. Each project follows the same proven methodology: bit-exact golden reference → pymodel → SystemVerilog RTL → cocotb verification → Yosys synthesis → OpenROAD P&R → 7nm GDSII.

---

## What KemetCore Is (and Is Not)

**What it is:**
- A laboratory for open-source silicon methodology.
- A collection of 11 highly-verified, independent hardware accelerators.
- A demonstration of a rigid `golden model → RTL → Formal/Simulation → GDSII` pipeline using open-source tools.
- Educational, modular, and bit-exact by design.

**What it is NOT:**
- **Not a bootable SoC (Yet):** The cores are currently standalone macros. RaCore (the SoC fabric that ties them together with a NoC, memory, and CPU) is planned but not fully integrated. You cannot boot an OS on KemetCore today.
- **Not Production-Ready for Tapeout:** The GDSII outputs are proofs-of-concept for the ASIC flow (routing density, area, Fmax). They do **not** include production constraints like DFT (Design for Test) scan chains, CDC (Clock Domain Crossing) synchronizers for external interfaces, padrings, or power-grid signoff. Do not tape these out without a backend physical design team.

---

## The KemetCore Philosophy

| Principle | What It Means |
|-----------|---------------|
| **Bit-Exact First** | Every RTL module must match a Python golden reference at the bit level. No tolerances, no approximations. |
| **pymodel Before RTL** | The cycle-level Python model is the specification. SystemVerilog is an implementation detail. |
| **Silicon or Bust** | Every project targets actual GDSII on ASAP7 7nm. Synthesis and P&R are not optional. |
| **Honest Engineering** | Public failure logs, documented workarounds, zero masked timing violations. No paper secrets. |
| **100% Test Coverage** | Directed edge cases + random fuzzing + exhaustive where feasible. Every test is a CI gate. |
| **Composable by Default** | Every block implements the same [KAI](docs/00_RaCore_SoC.md) interface, so any accelerator drops into the RaCore SoC with zero glue logic — one driver, one testbench skeleton, one conformance suite. |

---

## The Capstone — RaCore

The ten building blocks below are each a verified, taped-out accelerator. **[RaCore](docs/00_RaCore_SoC.md)** is the project that makes them a *computer*: a heterogeneous AI SoC that integrates all eleven cores (the ten below + the completed PtahCore) over a shared interconnect, with a common accelerator interface and a post-quantum root of trust.

| # | Project | Domain | Deity | Est. Complexity |
|---|---------|--------|-------|:---:|
| 00 | [**RaCore**](docs/00_RaCore_SoC.md) | **SoC — full-chip integration of all cores** | Ra (the supreme creator god) | ★★★★★ |

Three things RaCore adds that no single block has:
- **KAI (Kemet Accelerator Interface)** — one register + DMA contract every core implements, so blocks drop into the SoC with zero glue and one shared driver/testbench.
- **A real interconnect + memory hierarchy** — NoC, banked scratchpad, descriptor DMA: the actual throughput story.
- **A post-quantum security enclave** — AnubisCore + NeithCore compose into secure boot + attestation.

Built in two honest tiers: **RaCore-Lite** (~3.5 mm², GDSII-feasible on a 16 GB laptop) and **RaCore-Full** (~16 mm², a real shuttle target).

---

## The Ten Building Blocks

| # | Project | Domain | Deity | Est. Complexity |
|---|---------|--------|-------|:---:|
| 01 | [**SethCore**](docs/01_SethCore_RV32IM_CPU.md) | CPU — RV32IM pipelined core | Seth (god of chaos/strength) | ★★★★☆ |
| 02 | [**PtahConv**](docs/02_PtahConv_Convolution.md) | ML — Direct convolution accelerator | Ptah (god of craftsmen) | ★★★☆☆ |
| 03 | [**ImentetCore**](docs/03_ImentetCore_Attention.md) | ML — Transformer attention unit | Imentet (goddess of welcome) | ★★★☆☆ |
| 04 | [**GebCore**](docs/04_GebCore_SparseMatmul.md) | ML — 2:4 structured sparse matmul | Geb (god of the earth) | ★★★☆☆ |
| 05 | [**BastCore**](docs/05_BastCore_BF16Tensor.md) | ML — BF16 tensor core | Bastet (goddess of protection) | ★★☆☆☆ |
| 06 | [**AnubisCore**](docs/06_AnubisCore_HashEngine.md) | Crypto — SHA-256/SHA-3 hash engine | Anubis (god of embalming) | ★★☆☆☆ |
| 07 | [**NeithCore**](docs/07_NeithCore_MLKEM.md) | Crypto — ML-KEM (Kyber) lattice KEM | Neith (goddess of war/wisdom) | ★★★★☆ |
| 08 | [**SobekCore**](docs/08_SobekCore_RayTrace.md) | Graphics — Ray-triangle intersector | Sobek (god of the Nile) | ★★★☆☆ |
| 09 | [**HapiCore**](docs/09_HapiCore_FPU.md) | Arithmetic — IEEE-754 FPU generator | Hapi (god of the Nile flood) | ★★☆☆☆ |
| 10 | [**AtumCore**](docs/10_AtumCore_RVV.md) | CPU — RISC-V Vector Extension v1.0 | Atum (the creator god) | ★★★★★ |

---

## Project Comparison Matrix

| Metric | SethCore | PtahConv | ImentetCore | GebCore | BastCore | AnubisCore | NeithCore | SobekCore | HapiCore | AtumCore |
|--------|:--------:|:--------:|:-----------:|:-------:|:--------:|:----------:|:---------:|:---------:|:--------:|:--------:|
| **RTL Modules** | ~25 | ~12 | ~10 | ~8 | ~10 | ~6 | ~15 | ~8 | ~8 | ~20+ |
| **Tests (estimate)** | ~80 | ~40 | ~35 | ~30 | ~35 | ~25 | ~50 | ~35 | ~60 | ~100+ |
| **Fmax Target** | 500 MHz | 250 MHz | 250 MHz | 250 MHz | 250 MHz | 1 GHz | 200 MHz | 500 MHz | 500 MHz | 500 MHz |
| **Gate Count** | ~50K | ~6M | ~3M | ~4M | ~4M | ~15K | ~100K | ~30K | ~30K | ~100K+ |
| **GDSII Area** | ~0.1 mm² | ~3 mm² | ~1.5 mm² | ~2 mm² | ~2 mm² | ~0.05 mm² | ~0.3 mm² | ~0.08 mm² | ~0.1 mm² | ~0.5 mm² |
| **Depends on PtahCore** | No | Yes | Yes | Yes | Yes | No | No | No | Yes | Yes |
| **Novelty vs. Prior Art** | ★★★ | ★★★★ | ★★★ | ★★★★ | ★★ | ★★ | ★★★ | ★★★ | ★★ | ★★★ |

---

## How It All Fits Together

```
                      ┌──────────── RaCore SoC (capstone) ───────────┐
                      │                                              │
   CPU complex ──▶    │  SethCore (RV32IM) + AtumCore (RVV vector)   │
                      │                    │                          │
                      │            ┌───────▼────────┐                 │
   shared fabric ─▶   │            │  KAI NoC + DMA  │                 │
                      │            └───────┬────────┘                 │
                      │     ┌──────────────┼───────────────┐          │
   ML cluster ──▶     │  PtahCore Bast PtahConv Geb Imentet │  Sobek   │
                      │  (FP8) (BF16)(conv)(sparse)(attn)   │  (gfx)   │
                      │                    │                          │
   security ──▶       │  AnubisCore + NeithCore = PQ root of trust    │
   shared math ─▶     │  HapiCore (FPU library, used everywhere)      │
                      └──────────────────────────────────────────────┘
```

Every block speaks **KAI**, so the same host driver and the same cocotb testbench skeleton drive all of them. Integration cost scales with the *number of blocks*, not the *number of gates* — RaCore hardens each accelerator into a macro once, then routes only the top-level fabric. See [docs/00_RaCore_SoC.md](docs/00_RaCore_SoC.md).

---

## Verification Methodology

Every project in KemetCore follows the same 4-layer verification hierarchy:

```
Layer 4: SILICON — GDSII signoff (DRC clean, timing closed)
     ↑
Layer 3: RTL TESTS — cocotb + Verilator (52–100+ tests per project)
     ↑
Layer 2: PYMODE L — Cycle-level Python model (bit-exact vs golden)
     ↑
Layer 1: GOLDEN — Pure numpy golden reference (the mathematical truth)
```

**Tools used across all projects:**
- **Golden models:** Python 3.11+, numpy, scipy (as needed)
- **pymodel:** Pure Python with dataclasses, no hardware dependencies
- **RTL:** SystemVerilog (IEEE 1800-2017)
- **Simulation:** Verilator 5 with cocotb 1.9+
- **Synthesis:** Yosys
- **P&R:** OpenROAD-flow-scripts (ORFS) on ASAP7 7nm PDK
- **CI:** GitHub Actions

---

## What Exists Today (PtahCore)

PtahCore — the FP8 tensor accelerator — is already complete and serves as the blueprint:

- ✅ 112 files across golden/, pymodel/, rtl/, synth/, flow/, docs/
- ✅ 89 tests (52 RTL + 37 Python), all passing
- ✅ Yosys synthesis with 0 latches
- ✅ 5 GDSII macros on ASAP7: mac_cell, mac_tile, mac_row, mac_row_abut, mac_grid
- ✅ 32×32 array: 2.27 mm², 250 MHz, DRC clean, setup +1156 ps

Everything in KemetCore inherits this methodology and toolchain.

---

## Getting Started

```bash
# Prerequisites
python 3.11+    # Golden models + pymodels
verilator 5     # RTL simulation
cocotb 1.9+     # Testbench framework
yosys           # Synthesis
openroad        # Place & route (via ORFS Docker)

# Clone and explore
git clone https://github.com/Lord1Egypt/KemetCore.git
cd KemetCore

# Run every project's Phase 0/1 golden+pymodel tests (pure Python, <0.5 GB RAM)
pip install numpy pytest
pytest projects/ -q                # 54 tests across all 11 cores
python tools/test_all.py           # same, with a per-run summary

# Track / resume work
cat PROGRESS.md                    # master roadmap + mapping + RAM budget + resume guide
python tools/gen_tracking.py       # regenerate all tracking docs from tools/manifest.py
```

## Status: Phase 0/1 is live (Python), Phase 2+ (RTL→GDSII) is planned

Every one of the 11 cores has a **bit-exact golden reference** and a **cycle/lane/round
pymodel** implemented in pure Python with passing tests — RAM-trivial and runnable today.
The RAM-heavy RTL→GDSII phases are mapped but not started. See **[PROGRESS.md](PROGRESS.md)**
for the full matrix, per-project `STEPS.md` / `CHECKPOINTS.md` / `TESTS.md`, and the
per-phase RAM budget.

---

## Project Lifecycle

Each project progresses through 6 phases:

```
Phase 0: Spec & Golden — Architecture document, golden reference in numpy
Phase 1: pymodel     — Cycle-level behavioral model, pymodel tests
Phase 2: RTL         — SystemVerilog implementation, cocotb tests
Phase 3: Synthesis   — Yosys elaboration, gate count, latch checks
Phase 4: P&R         — OpenROAD floorplan → GDSII
Phase 5: Signoff     — Timing closure, DRC clean, CI pipeline
```

See [ROADMAP.md](ROADMAP.md) for the current status of all projects.

---

## License

All projects in KemetCore are released under the [Apache License 2.0](LICENSE) unless otherwise noted.

---

## About the Author

Built by [Mohamed Mounir](https://github.com/Lord1Egypt). Debian → SystemVerilog → Go → Python. believes in open-source silicon, Egyptian mythology naming conventions, and testing everything to destruction.
