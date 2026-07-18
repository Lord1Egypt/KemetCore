# ImentetCore — TESTS

_Auto-generated from `tools/manifest.py`._

Run: `pytest projects/imentetcore/tests -v`

| Test | Verifies | Status |
|------|----------|:------:|
| `test_attention_vs_reference` | attention == numpy reference | ✅ |
| `test_softmax_stable` | softmax(x) == softmax(x+c), no overflow | ✅ |
| `test_flash_equals_golden` | tiled flash attention == golden | ✅ |
| `test_causal_mask` | causal mask zeroes future positions | ✅ |
| `rtl: test_core (cocotb)` | imentet_core == golden.attention on 10 random blocks | ✅ |

**5/5 tests passing.**
