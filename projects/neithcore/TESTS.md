# NeithCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/neithcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_ntt_roundtrip` | intt(ntt(p)) == p | ✅ |
| `test_ntt_polymult` | NTT product == negacyclic schoolbook | ✅ |
| `test_kem_correctness` | decaps(encaps) == shared secret over many trials | ✅ |
| `test_pymodel_ntt` | staged butterfly == golden NTT | ✅ |
| `rtl: test_modmul (cocotb)` | neith_modmul == (a*b)%7681 on 31K+ vectors | ✅ |
| `rtl: test_butterfly (cocotb)` | neith_butterfly == golden CT butterfly on 32K+ | ✅ |
| `rtl: test_ntt (cocotb)` | neith_ntt == golden.ntt_cyclic on 28 transforms | ✅ |

**7/7 tests passing.**
