# HapiCore RTL (Phase 2)

Combinational floating-point datapath — the primitives every KemetCore ML block
(BastCore, GebCore, PtahConv, …) is built from. Two formats so far: **bf16**
(`[15] sign | [14:7] exp bias-127 | [6:0] mant`) and **fp32 / binary32**
(`[31] sign | [30:23] exp bias-127 | [22:0] mant`). The fp32 cores reuse the exact
bf16 algorithms widened to a 24-bit significand; `hapi_fp32_add` is what the
BastCore tensor core needs for its fp32 accumulate.

`hapi_bf16_mul.sv` / `hapi_fp32_mul.sv` — single-cycle multiplier. Exact N×N
significand product, leading-zero normalise, round-to-nearest-ties-to-even, with
full special-value handling (NaN propagation, Inf×0 → NaN, x×0 → 0), subnormal
**inputs and outputs**, overflow → Inf and underflow → subnormal/zero.

`hapi_bf16_add.sv` / `hapi_fp32_add.sv` — single-cycle adder. Larger-magnitude
operand selected by an unsigned compare of `{exp,mantissa}`, small operand aligned
with guard/round/sticky, effective add/subtract, leading-zero normalise + RNE.
Handles cancellation (`x + (-x) = +0`), signed-zero rules, Inf+Inf(opposite) → NaN,
subnormals, and overflow/underflow.

## Interfaces
| Core | Inputs | Output |
|------|--------|--------|
| `hapi_bf16_mul` / `hapi_bf16_add` | `a[15:0]`, `b[15:0]` | `y[15:0]` |
| `hapi_fp32_mul` / `hapi_fp32_add` | `a[31:0]`, `b[31:0]` | `y[31:0]` |

All combinational.

## Run the testbenches (cocotb + Verilator)
```bash
cd projects/hapicore/rtl/tb
./run_sim.sh CORE=mul        # bf16 multiplier
./run_sim.sh CORE=add        # bf16 adder
./run_sim.sh CORE=fp32mul    # fp32 multiplier
./run_sim.sh CORE=fp32add    # fp32 adder
```
`run_sim.sh` forces a single consistent Python (handles conda-cocotb vs
system-verilator). All four are verified **bit-exact** against the Python golden /
numpy fp32 (RNE-correct): bf16 mul over 576 corners + 6,000 random + 512 edges; bf16
add over 625 + 6,000 + ~5,954 cancellation + 392 edges; fp32 mul over 576 + 40,000 +
512 edges; fp32 add over 576 + 40,000 + ~29,744 cancellation + 392 edges. NaN results
compared by class (payload bits are not architectural); the sign of zero **is** checked.

## Status
- ✅ Phase 2: bf16 + fp32 multiplier RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: bf16 + fp32 adder RTL + cocotb
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
- ⬜ Next: fp16 datapath, fused multiply-add, divide (Goldschmidt), then ASAP7
