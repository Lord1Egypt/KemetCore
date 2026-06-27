# HapiCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/hapicore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_add_matches_numpy` | fp16/fp32 add == numpy IEEE result | ✅ |
| `test_bf16_round_cases` | hand-computed bf16 RNE cases | ✅ |
| `test_mul_commutative` | a*b == b*a across formats | ✅ |
| `test_fma_more_accurate` | fma beats separate mul+add on a known case | ✅ |
| `test_specials` | NaN/Inf propagation + signed zero | ✅ |
| `test_pymodel_latency` | pipeline reports correct cycle latency | ✅ |

**6/6 tests passing.**
