# HapiCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/hapicore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_add_matches_numpy` | fp16/fp32 add == numpy IEEE result | ✅ |
| `test_bf16_round_cases` | hand-computed bf16 RNE cases | ✅ |
| `test_mul_commutative` | a*b == b*a across formats | ✅ |
| `test_fma_more_accurate` | fma beats separate mul+add on a known case | ✅ |
| `test_fma_single_rounded` | fma == nearest fp32 of exact a*b+c (4K random) | ✅ |
| `test_fma_specials` | fma 0*Inf/Inf-Inf->NaN, overflow, exact subnormal | ✅ |
| `test_div_single_rounded` | div == nearest fp32 of exact a/b (4K random) | ✅ |
| `test_div_specials` | div x/0->Inf, 0/0 & Inf/Inf->NaN, finite/Inf->signed 0 | ✅ |
| `test_specials` | NaN/Inf propagation + signed zero | ✅ |
| `test_pymodel_latency` | pipeline reports correct cycle latency | ✅ |
| `rtl: test_fp16_mul (cocotb)` | hapi_fp16_mul == golden.fp_mul fp16 on corners+8K+edges | ✅ |
| `rtl: test_fp16_add (cocotb)` | hapi_fp16_add == golden.fp_add fp16 on corners+8K+3K-cancel+edges | ✅ |
| `rtl: test_bf16_mul (cocotb)` | hapi_bf16_mul == golden on 7K+ products | ✅ |
| `rtl: test_bf16_add (cocotb)` | hapi_bf16_add == golden on 12K+ sums | ✅ |
| `rtl: test_fp32_mul (cocotb)` | hapi_fp32_mul == numpy fp32 on 40K+ products | ✅ |
| `rtl: test_fp32_add (cocotb)` | hapi_fp32_add == numpy fp32 on 70K+ sums | ✅ |
| `rtl: test_fp32_fma (cocotb)` | hapi_fp32_fma == single-rounded golden on 54K+ FMAs | ✅ |
| `rtl: test_bf16_fma (cocotb)` | hapi_bf16_fma == single-rounded golden on 150K+ FMAs | ✅ |
| `rtl: test_fp16_fma (cocotb)` | hapi_fp16_fma == single-rounded golden on 150K+ FMAs | ✅ |
| `rtl: test_fp32_div (cocotb)` | hapi_fp32_div == correctly-rounded golden on 165K+ divisions | ✅ |

**20/20 tests passing.**
