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
| `rtl: test_valu (cocotb)` | atum_valu.sv (add/sub/mul/logic/shift + vmacc) == golden on corners + 6000 random (all ops/vl/mask) | ✅ |
| `rtl: test_vfpu (cocotb)` | atum_vfpu.sv (fp32 vfadd/vfmul) == golden on fp corners + 5000 random | ✅ |
| `rtl: test_vredu (cocotb)` | atum_vredu.sv (vredsum/vredmax) == golden on directed + 6000 random | ✅ |
| `rtl: test_vexec (cocotb)` | atum_vexec.sv integrated unit == golden on directed + 6000 random mixed ALU/FP/RED ops | ✅ |

**10/10 tests passing.**
