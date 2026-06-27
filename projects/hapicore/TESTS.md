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
| `rtl: test_bf16_mul (cocotb)` | hapi_bf16_mul == golden on 7K+ products | ✅ |
| `rtl: test_bf16_add (cocotb)` | hapi_bf16_add == golden on 12K+ sums | ✅ |
| `rtl: test_fp32_mul (cocotb)` | hapi_fp32_mul == numpy fp32 on 40K+ products | ✅ |
| `rtl: test_fp32_add (cocotb)` | hapi_fp32_add == numpy fp32 on 70K+ sums | ✅ |

**10/10 tests passing.**
