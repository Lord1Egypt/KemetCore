# PtahConv — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/ptahconv/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_conv_vs_reference` | im2col conv == naive loop reference | ✅ |
| `test_stride_pad` | stride=2,pad=1 shapes + values correct | ✅ |
| `test_pymodel_equals_golden` | tiled dataflow == golden | ✅ |

**3/3 tests passing.**
