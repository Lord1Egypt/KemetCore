# NeithCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| N.1 | P0 | Golden: NTT mod 7681 + inverse (roundtrip) | ✅ |
| N.2 | P0 | Golden: NTT polymult == schoolbook | ✅ |
| N.3 | P0 | Golden: KEM keygen/encaps/decaps (self-consistent) | ✅ |
| N.4 | P1 | pymodel: NTT butterfly stages | ✅ |
| N.5 | P2 | RTL: modular multiplier (Barrett) + cocotb vs golden | ✅ |
| N.6 | P2 | RTL: Cooley-Tukey butterfly + cocotb vs golden | ✅ |
| N.7 | P2 | RTL: 256-pt NTT engine, forward + inverse (+1/N scale) + cocotb | ✅ |
| N.8 | P2 | RTL: psi pre/post-multiply for full negacyclic ntt()/intt() | ✅ |
| N.9 | P3 | Synthesis: generic Yosys, 0 latches + gate count | ✅ |
| N.10 | P3 | Synthesis: ASAP7 liberty tech-mapping + SRAM macro (subsumed by P&R) | ✅ |
| N.11 | P4 | P&R: GDSII | ✅ |
| N.12 | P5 | Signoff: formal proof of Barrett modmul range r<Q — always a valid reduced field element (yosys-smtbmc+z3, all a,b<Q) | 🔧 |
| N.13 | P5 | Signoff: formal control-safety of the 256-pt NTT FSM — no illegal state + inverse-only scale pass (temporal k-induction, mutation-tested) | 🔧 |

**Progress:** 11/13 checkpoints complete (100% of phases).
