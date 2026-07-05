# AtumCore — CHECKPOINTS

_Auto-generated from `tools/manifest.py`._

| ID | Phase | Checkpoint | Status |
|----|:-----:|------------|:------:|
| AT.1 | P0 | Golden: RVV subset + vsetvl semantics | ✅ |
| AT.2 | P0 | Golden: masked ops + reductions | ✅ |
| AT.3 | P1 | pymodel: 8 ALU lanes | ✅ |
| AT.4 | P1 | pymodel: strip-mined axpy | ✅ |
| AT.6 | P2 | RTL: vector integer ALU lane array (atum_valu, incl vmacc) + cocotb vs golden | ✅ |
| AT.8 | P2 | RTL: fp32 vector lane (atum_vfpu, vfadd/vfmul over HapiCore fp32) + cocotb | ✅ |
| AT.9 | P2 | RTL: vector reduction unit (atum_vredu, vredsum/vredmax) + cocotb | ✅ |
| AT.10 | P2 | RTL: integrated vector execute unit (atum_vexec) + cocotb vs golden | ✅ |
| AT.11 | P2 | RTL: vector register file (atum_vregfile) + vsetvl (atum_vsetvl) + cocotb | ✅ |
| AT.12 | P2 | RTL: single-cycle vector core (atum_vcore) + vector memory (VLD/VST) running strip-mined programs | ✅ |
| AT.13 | P4 | P&R: GDSII at 500 MHz | 🔧 |
| AT.14 | P5 | Signoff: formal proof of atum_valu lane algebra (yosys-smtbmc+z3, exhaustive) | 🔧 |

**Progress:** 10/12 checkpoints complete (33% of phases).
