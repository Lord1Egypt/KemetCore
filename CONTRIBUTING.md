# 🤝 Contributing to KemetCore

KemetCore is an open-source silicon laboratory. Every contribution — whether a bug fix, a new RTL module, documentation, or a test — strengthens the ecosystem.

## 🧱 Before You Start

Check [PROGRESS.md](PROGRESS.md) to see which phase each project is in. Phase 0 (golden) and Phase 1 (pymodel) are complete for all cores — contributions are most impactful on **Phases 2-5 (RTL → Synthesis → P&R → GDSII)**.

## 🚀 Getting Started

```bash
git clone https://github.com/Lord1Egypt/KemetCore.git
cd KemetCore
pip install numpy pytest
pytest projects/ -q   # all golden + pymodel tests must pass
```

## 📐 Methodology

Every core follows the 4-layer verification hierarchy:

```
Layer 1: GOLDEN  — Pure numpy golden reference (the mathematical truth)
Layer 2: PYMODE  — Cycle-level Python model, bit-exact vs golden
Layer 3: RTL     — SystemVerilog + cocotb tests (Verilator)
Layer 4: SILICON — Yosys synthesis → OpenROAD P&R → GDSII
```

**Rule:** RTL is never written before the pymodel exists and passes against the golden.

## 🧪 Tests

```bash
# Phase 0/1 (pure Python, fast)
pytest projects/ -v

# Phase 2 (requires Verilator + cocotb)
cd projects/[project]/rtl/tb && bash run_sim.sh CORE=[module]
```

## 📋 Pull Request Checklist

- [ ] Does your code follow the project's methodology (golden → pymodel → RTL)?
- [ ] Are there passing tests for every new module?
- [ ] Does `pytest projects/ -q` still pass?
- [ ] Have you updated the relevant `STEPS.md` / `CHECKPOINTS.md`?
- [ ] Is the SystemVerilog lint-free (no latches on synth)?

## ❓ Questions?

Open a [Discussion](https://github.com/Lord1Egypt/KemetCore/discussions) or an [Issue](https://github.com/Lord1Egypt/KemetCore/issues).

---

By contributing, you agree that your contributions are licensed under [Apache 2.0](LICENSE).
