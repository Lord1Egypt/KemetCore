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
| N.7 | P2 | RTL: multicycle 256-point NTT engine | ⬜ |
| N.8 | P3 | Synthesis: generic Yosys, 0 latches + gate count | ✅ |
| N.9 | P3 | Synthesis: ASAP7 liberty tech-mapping | ⬜ |
| N.10 | P4 | P&R: GDSII | ⬜ |

**Progress:** 7/10 checkpoints complete (33% of phases).
