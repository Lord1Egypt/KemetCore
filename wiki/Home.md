# 𓆎 Welcome to KemetCore

> *"From RTL to GDSII. Every project starts with a golden model, ends with silicon."*
>
> **KemetCore** is an open-source silicon laboratory — a collection of 10 hardware accelerator projects spanning CPUs, ML accelerators, cryptographic engines, graphics, and more, plus a capstone AI SoC (RaCore) that integrates them all into a single chip.

Named after **Kemet** (𓆎𓅓𓏏𓊖) — the ancient Egyptian name for Egypt, meaning "the black land."

---

## 🌍 What is this?

KemetCore designs, verifies, synthesizes, and places-and-routes **real digital hardware** from SystemVerilog RTL all the way to 7nm GDSII layouts. Every project follows the same rigorous flow:

```
Golden Model (numpy) → pymodel (Python) → RTL (SystemVerilog) → cocotb Tests → Yosys Synthesis → OpenROAD P&R → GDSII
```

**This is not a paper architecture.** 516 files, ~1 million lines of code, 108+ merged PRs, all CI green. Real code, real synthesis, real silicon path.

---

## 🏛️ The Six Pillars

| # | Principle | What It Means |
|---|-----------|---------------|
| 🎯 | **Bit-Exact First** | Every RTL module matches a Python golden reference at the bit level. No tolerances, no approximations. |
| 📐 | **pymodel Before RTL** | The cycle-level Python model IS the specification. SystemVerilog is an implementation detail. |
| ⚡ | **Silicon or Bust** | Every project targets actual GDSII on ASAP7 7nm. Synthesis and P&R are not optional. |
| 🔍 | **Honest Engineering** | Public failure logs, documented workarounds, zero masked timing violations. No paper secrets. |
| 🧪 | **100% Test Coverage** | Directed edge cases + random fuzzing + exhaustive where feasible. Every test is a CI gate. |
| 🧩 | **Composable by Default** | Every block implements the same KAI interface, so any accelerator drops into RaCore with zero glue logic. |

---

## 🗺️ The 11 Cores

| # | Core | Domain | Deity |
|:-:|------|--------|-------|
| 00 | **RaCore** | AI SoC — full-chip integration | Ra (supreme creator) |
| 01 | **SethCore** | RISC-V RV32IM pipelined CPU | Seth (chaos/strength) |
| 02 | **PtahConv** | ML — direct convolution | Ptah (craftsmen) |
| 03 | **ImentetCore** | ML — transformer attention | Imentet (welcome/afterlife) |
| 04 | **GebCore** | ML — 2:4 structured sparse matmul | Geb (earth) |
| 05 | **BastCore** | ML — BF16 tensor core | Bastet (protection) |
| 06 | **AnubisCore** | Crypto — SHA-256/SHA-3 engine | Anubis (embalming) |
| 07 | **NeithCore** | Crypto — ML-KEM (Kyber) KEM | Neith (war/wisdom) |
| 08 | **SobekCore** | Graphics — ray-triangle intersector | Sobek (Nile/crocodiles) |
| 09 | **HapiCore** | Arithmetic — IEEE-754 FPU library | Hapi (Nile flood) |
| 10 | **AtumCore** | CPU — RISC-V Vector Extension v1.0 | Atum (creator) |

---

## 📊 Project Status

**Overall: Phase 0/1 complete across all 11 cores** — bit-exact golden references + cycle-level pymodels with passing tests. RTL is actively shipping for multiple cores (AnubisCore, NeithCore, HapiCore, RaCore, PtahConv, AtumCore).

All pure-Python tests run on any laptop (`pip install numpy pytest && pytest projects/ -q`). The heavy RTL→GDSII phases are RAM-mapped and ready: the first tape-outs (AnubisCore, HapiCore) are achievable on a typical 16 GB laptop.

---

## 🛠️ Tools & Stack

| Layer | Tool | Version |
|-------|------|---------|
| Golden models | Python + numpy | 3.11+ |
| RTL | SystemVerilog | IEEE 1800-2017 |
| Simulation | Verilator + cocotb | 5 / 1.9+ |
| Synthesis | Yosys | latest |
| P&R | OpenROAD-flow-scripts | latest |
| PDK | ASAP7 | 7nm |
| CI | GitHub Actions | — |

---

## 👤 Author

Built by [Mohamed Mounir](https://github.com/Lord1Egypt). Debian → SystemVerilog → Go → Python. Believes in open-source silicon, Egyptian mythology naming conventions, and testing everything to destruction.

---

### 🚀 Quick Start

```bash
git clone https://github.com/Lord1Egypt/KemetCore.git
cd KemetCore
pip install numpy pytest
pytest projects/ -q    # 54+ tests, all green
```

**Browse the sidebar →** for detailed pages on every core, the methodology, progress tracking, and more.
