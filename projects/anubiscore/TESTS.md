# AnubisCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/anubiscore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_sha256_vs_hashlib` | random + fixed messages == hashlib.sha256 | ✅ |
| `test_sha3_256_vs_hashlib` | == hashlib.sha3_256 | ✅ |
| `test_known_vectors` | empty/'abc' digests match published values | ✅ |
| `test_pymodel_rounds` | round engine reproduces one-shot digest | ✅ |
| `rtl: test_vectors (cocotb)` | sha256_core.sv digest == golden on 9 msgs | ✅ |

**5/5 tests passing.**
