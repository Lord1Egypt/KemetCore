# GebCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/gebcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_sparse_equals_dense` | sparse matmul == dense matmul on 2:4 weights | ✅ |
| `test_compression_metadata` | 2-of-4 selection + indices correct | ✅ |
| `test_macs_halved` | pymodel performs ~50% of dense MACs | ✅ |
| `rtl: test_spmac (cocotb)` | geb_spmac == golden.sparse_matmul on 412 elements | ✅ |
| `rtl: test_spmac_grid (cocotb)` | geb_spmac_grid 4x4 == golden.sparse_matmul on 40 random 2:4 matmuls | ✅ |

**5/5 tests passing.**
