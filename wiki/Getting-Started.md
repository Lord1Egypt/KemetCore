# 👨‍💻 Getting Started

Get KemetCore running on your machine in under 5 minutes.

---

## Prerequisites

```bash
python 3.11+       # Golden models + pymodels (REQUIRED)
verilator 5        # RTL simulation (optional, for Phase 2+)
cocotb 1.9+        # Testbench framework (optional, for Phase 2+)
yosys              # Synthesis (optional, for Phase 3+)
openroad           # Place & route via ORFS Docker (optional, for Phase 4+)
```

**Phase 0/1 (Python only):** just Python 3.11+ and numpy. No Verilator, no Yosys, no OpenROAD. Everything fits on any laptop.

---

## Clone & Set Up

```bash
git clone https://github.com/Lord1Egypt/KemetCore.git
cd KemetCore
pip install numpy pytest
```

---

## Running Tests

### All Phase 0/1 Tests (Python, fast, recommended)
```bash
pytest projects/ -q
```
Expect: 54+ tests, all green. Runs in seconds, uses <0.5 GB RAM.

### Per-Project Tests
```bash
pytest projects/anubiscore/tests -v    # AnubisCore hash engine
pytest projects/hapicore/tests -v      # HapiCore FPU
pytest projects/neithcore/tests -v     # NeithCore ML-KEM
# ... etc for all 11 projects
```

### Summary Runner
```bash
python tools/test_all.py    # Per-run summary of all projects
```

---

## Project Structure

```
KemetCore/
├── docs/                 # Architecture specs for all 11 cores
│   ├── 00_RaCore_SoC.md
│   ├── 01_SethCore_RV32IM_CPU.md
│   └── ...
├── projects/             # One subdirectory per core
│   ├── anubiscore/       # golden/, pymodel/, rtl/, synth/, tests/
│   ├── atumcore/
│   ├── bastcore/
│   ├── gebcore/
│   ├── hapicore/
│   ├── imentetcore/
│   ├── neithcore/
│   ├── ptahconv/
│   ├── racore/
│   ├── sethcore/
│   └── sobekcore/
├── tools/                # Manifest, tracking generator, test runner
├── PROGRESS.md           # Master progress + RAM budget + resume guide
├── ROADMAP.md            # Phased execution plan
├── conftest.py           # pytest configuration
└── pytest.ini            # pytest settings
```

Each project directory:
```
projects/<core>/
├── golden/       # Pure numpy golden reference
├── pymodel/      # Cycle-level Python behavioral model
├── rtl/          # SystemVerilog RTL + cocotb testbenches
├── synth/        # Yosys synthesis scripts + reports
├── flow/         # OpenROAD P&R scripts
├── tests/        # pytest suite
├── STEPS.md      # Per-phase implementation steps
├── CHECKPOINTS.md # Phase gating criteria
└── TESTS.md      # Test plan
```

---

## Tracking Progress

```bash
cat PROGRESS.md                    # Master matrix + RAM budget + resume guide
python tools/gen_tracking.py       # Regenerate all tracking docs from manifest
python tools/manifest.py           # (data only; edit to update status)
```

---

## Running Individual Cores

### AnubisCore — SHA-256/SHA-3 RTL Tests
```bash
cd projects/anubiscore/rtl/tb
make              # run all cocotb tests
```

### AnubisCore — Synthesis
```bash
cd projects/anubiscore/synth
bash run_synth.sh   # Yosys elaboration
```

---

## CI Pipeline

KemetCore uses GitHub Actions. Every PR triggers:
1. **Golden tests** — `pytest projects/*/golden`
2. **pymodel tests** — `pytest projects/*/pymodel`
3. **RTL tests** — cocotb + Verilator
4. **Synthesis checks** — Yosys latch checks (all `make all`)

All 108+ merged PRs passed CI. The streak is unbroken.

---

## Build Order

If you're implementing new RTL, follow the dependency order:
```
HapiCore, AnubisCore → BastCore, SethCore → PtahConv, GebCore
→ ImentetCore
SobekCore, NeithCore (independent)
AtumCore → RaCore (capstone)
```
