# NeithCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/neithcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_ntt_roundtrip` | intt(ntt(p)) == p | ✅ |
| `test_ntt_polymult` | NTT product == negacyclic schoolbook | ✅ |
| `test_kem_correctness` | decaps(encaps) == shared secret over many trials | ✅ |
| `test_pymodel_ntt` | staged butterfly == golden NTT | ✅ |

**4/4 tests passing.**
