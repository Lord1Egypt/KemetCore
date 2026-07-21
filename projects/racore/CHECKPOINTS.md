# RaCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| RA.1 | P0 | Golden: KAI register model + conformance harness | ✅ |
| RA.2 | P0 | Golden: NoC crossbar + descriptor DMA | ✅ |
| RA.3 | P0 | Golden: end-to-end axpy over KAI | ✅ |
| RA.4 | P1 | pymodel: arbitration + DMA timing | ✅ |
| RA.5 | P2 | RTL: NoC + DMA | ✅ |
| RA.7 | P2 | RTL: RaCore-Lite top integration | ✅ |
| RA.8 | P3 | Synth: RaCore-Lite top integration | ✅ |
| RA.10 | P4 | P&R: Lite hierarchical GDSII | ✅ |
| RA.11 | P5 | Signoff: formal proof of NoC arbiter grant safety (k-induction, yosys-smtbmc+z3) | 🔧 |
| RA.11 | P5 | Flagship demo: CNN inference + attestation | ⬜ |

**Progress:** 8/10 checkpoints complete (50% of phases).
