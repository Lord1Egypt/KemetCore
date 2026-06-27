# SethCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/sethcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_arith_program` | sum-1..10 loop returns 55 | ✅ |
| `test_fibonacci` | fib(10) == 55 | ✅ |
| `test_mul_div` | mul/div/rem match Python semantics | ✅ |
| `test_branches` | beq/bne/blt/bge taken correctly | ✅ |
| `test_pymodel_equals_golden` | pipeline result == ISA sim | ✅ |
| `rtl: test_alu (cocotb)` | seth_alu.sv == golden _alu_r on all ops | ✅ |

**6/6 tests passing.**
