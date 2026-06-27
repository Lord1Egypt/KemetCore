# SobekCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/sobekcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_hit_center` | ray through triangle centroid hits, t correct | ✅ |
| `test_miss` | ray outside triangle misses | ✅ |
| `test_parallel` | ray parallel to triangle plane -> no hit | ✅ |
| `test_barycentric` | u,v,w in [0,1] and sum to 1 on hit | ✅ |
| `test_pymodel_equals_golden` | pipeline == golden | ✅ |

**5/5 tests passing.**
