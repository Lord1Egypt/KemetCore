# RaCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/racore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_kai_conformance` | mock accel exposes mandatory KAI registers | ✅ |
| `test_dma_2d` | 2D/strided DMA copies correct bytes | ✅ |
| `test_noc_arbitration` | two masters share the crossbar fairly | ✅ |
| `test_axpy_end2end` | host->DMA->accel->host axpy == a*x+y | ✅ |

**4/4 tests passing.**
