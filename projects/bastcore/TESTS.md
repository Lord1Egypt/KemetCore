# BastCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/bastcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_matmul_vs_numpy` | bf16 matmul within bf16 tolerance of fp32 ref | ✅ |
| `test_identity` | A @ I == A (bf16 representable) | ✅ |
| `test_pymodel_equals_golden` | systolic pymodel == golden matmul | ✅ |

**3/3 tests passing.**
