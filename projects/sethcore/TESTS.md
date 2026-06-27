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
| `test_decode_imm_formats` | decode_imm sign-extends I/S/B/U/J correctly | ✅ |
| `rtl: test_alu (cocotb)` | seth_alu.sv == golden _alu_r on all ops | ✅ |
| `rtl: test_muldiv (cocotb)` | seth_muldiv.sv == golden _muldiv (incl edges) | ✅ |
| `rtl: test_imm (cocotb)` | seth_imm.sv == golden.decode_imm on 70K+ words | ✅ |

**9/9 tests passing.**
