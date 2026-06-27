# BastCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/bastcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_matmul_vs_numpy` | bf16 matmul within bf16 tolerance of fp32 ref | ✅ |
| `test_identity` | A @ I == A (bf16 representable) | ✅ |
| `test_pymodel_equals_golden` | systolic pymodel == golden matmul | ✅ |
| `rtl: test_mac (cocotb)` | bast_mac == golden.matmul on 400 dot products | ✅ |
| `rtl: test_mac_grid (cocotb)` | bast_mac_grid 4x4 == golden.matmul (directed + 60 random, K<=24) | ✅ |

**5/5 tests passing.**
