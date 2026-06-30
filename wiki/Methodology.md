# 🔬 Methodology

KemetCore follows a rigorous, proven methodology that ensures correctness at every stage. **No shortcuts, no approximations, no paper secrets.**

---

## The 4-Layer Verification Pyramid

```
Layer 4: SILICON — GDSII signoff (DRC clean, timing closed)
     ↑
Layer 3: RTL TESTS — cocotb + Verilator (25–100+ tests per project)
     ↑
Layer 2: PYMODE L — Cycle-level Python model (bit-exact vs golden)
     ↑
Layer 1: GOLDEN — Pure numpy golden reference (the mathematical truth)
```

### Layer 1: Golden Reference (numpy)
The mathematical truth. Pure Python + numpy. Verified against known-correct references (PyTorch for ML, hashlib for crypto, Spike for CPU, etc.). This is the specification — if the golden model says X, X is correct.

**Tools:** Python 3.11+, numpy, scipy  
**Runtime:** <0.5 GB RAM, seconds per test  
**State:** ✅ Complete for all 11 cores

### Layer 2: pymodel (Cycle-Level Model)
A cycle-accurate behavioral model in Python. Uses dataclasses and clock-level state machines. Must produce bit-identical results to the golden reference.

**Tools:** Pure Python, dataclasses, pytest  
**Runtime:** <0.5 GB RAM, seconds per test  
**State:** ✅ Complete for all 11 cores

### Layer 3: RTL Tests (cocotb + Verilator)
SystemVerilog hardware is simulated with Verilator and driven by cocotb Python testbenches. Every test compares RTL output against the corresponding pymodel output.

**Tools:** Verilator 5, cocotb 1.9+, SystemVerilog IEEE 1800-2017  
**Runtime:** 2–16 GB RAM, minutes per test suite  
**State:** 🔧 Active for AnubisCore, NeithCore, HapiCore, RaCore, AtumCore, PtahConv

### Layer 4: Silicon Signoff (Yosys + OpenROAD)
Synthesis with Yosys (0 latches enforced), place-and-route with OpenROAD-flow-scripts on ASAP7 7nm PDK. Must pass DRC and timing closure.

**Tools:** Yosys, OpenROAD, ASAP7 PDK  
**Runtime:** 4–20+ GB RAM, hours per design  
**State:** 🔧 Synthesis reports exist for AnubisCore; rest planned

---

## The 6-Phase Project Lifecycle

| Phase | Name | Deliverable | Exit Criteria |
|:-----:|------|-------------|---------------|
| **0** | Spec & Golden | Architecture document + golden reference (numpy) | All math verified against known-correct software |
| **1** | pymodel | Cycle-level Python behavioral model | pymodel passes all tests; tests reviewed |
| **2** | RTL | SystemVerilog implementation + cocotb tests | All RTL tests pass; coverage ≥90% |
| **3** | Synthesis | Yosys elaboration + gate-level netlist | 0 latches; ≤target gate count |
| **4** | P&R | OpenROAD floorplan → GDSII | DRC clean; timing closed at target Fmax |
| **5** | Signoff | CI pipeline + documentation finalization | `make all` passes; docs complete |

---

## The KemetCore Philosophy

| Principle | What It Means |
|-----------|---------------|
| **Bit-Exact First** | Every RTL module must match a Python golden reference at the bit level. No tolerances, no approximations. |
| **pymodel Before RTL** | The cycle-level Python model is the specification. SystemVerilog is an implementation detail. |
| **Silicon or Bust** | Every project targets actual GDSII on ASAP7 7nm. Synthesis and P&R are not optional. |
| **Honest Engineering** | Public failure logs, documented workarounds, zero masked timing violations. No paper secrets. |
| **100% Test Coverage** | Directed edge cases + random fuzzing + exhaustive where feasible. Every test is a CI gate. |
| **Composable by Default** | Every block implements the same KAI interface, so any accelerator drops into the RaCore SoC with zero glue logic — one driver, one testbench skeleton, one conformance suite. |

---

## RAM Budget for P&R

The real wall is OpenROAD detailed routing. Based on PtahCore's real data point (2.27 mm² flat ≈ 14 GB):

| Project | Area | GDSII Peak RAM | 16 GB Laptop? | Strategy |
|---------|------|:--------------:|:-------------:|----------|
| AnubisCore | 0.05 mm² | ~1.5 GB | ✅ | flat |
| SobekCore | 0.08 mm² | ~2 GB | ✅ | flat |
| HapiCore | 0.1 mm² | ~2 GB | ✅ | flat |
| SethCore | 0.1 mm² | ~2 GB | ✅ | flat |
| NeithCore | 0.3 mm² | ~3-4 GB | ✅ | flat |
| AtumCore | 0.5 mm² | ~5-6 GB | ✅ | flat |
| ImentetCore | 1.5 mm² | ~9-11 GB | ⚠️ | tile-abut |
| BastCore | 2.0 mm² | ~12-14 GB | ⚠️ | tile-abut |
| GebCore | 2.0 mm² | ~12-14 GB | ⚠️ | tile-abut |
| PtahConv | 3.0 mm² | ~18-20 GB | ❌ flat | **must** tile-abut |
| RaCore-Lite | 3.5 mm² | ~3-5 GB | ✅ | hierarchical |
| RaCore-Full | 16 mm² | ≥64 GB | ❌ | real iron |

**Key insight:** with tile-abutment, everything except RaCore-Full closes on a 16 GB laptop.
