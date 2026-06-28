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
| `rtl: test_valu (cocotb)` | atum_valu.sv == golden VectorUnit on corners + 6000 random (all ops/vl/mask) | ✅ |

**7/7 tests passing.**
