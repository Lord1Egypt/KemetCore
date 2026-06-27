# AtumCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/atumcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_vadd_vmul` | integer vector ops == numpy | ✅ |
| `test_vmacc` | fused multiply-accumulate == numpy | ✅ |
| `test_masked` | masked vadd only updates active lanes | ✅ |
| `test_vredsum` | reduction == numpy sum | ✅ |
| `test_vfmul_fp` | fp32 vector mul == numpy | ✅ |
| `test_axpy_stripmined` | strip-mined axpy == a*x+y | ✅ |

**6/6 tests passing.**
