# HapiCore RTL (Phase 2)

Combinational bfloat16 datapath — the two primitives every KemetCore ML block
(BastCore, GebCore, PtahConv, …) is built from. bf16 layout:
`[15] sign | [14:7] exponent (bias 127) | [6:0] mantissa`.

`hapi_bf16_mul.sv` — single-cycle bf16 multiplier. Exact 8×8 significand product,
leading-zero normalise, round-to-nearest-ties-to-even, with full special-value
handling (NaN propagation, Inf×0 → NaN, x×0 → 0), subnormal **inputs and outputs**,
overflow → Inf and underflow → subnormal/zero.

`hapi_bf16_add.sv` — single-cycle bf16 adder. Larger-magnitude operand selected by
an unsigned compare of `{exp,mantissa}`, small operand aligned with guard/round/
sticky, effective add/subtract, leading-zero normalise + RNE. Handles cancellation
(`x + (-x) = +0`), signed-zero rules, Inf+Inf(opposite) → NaN, subnormals, and
overflow/underflow.

## Interface (both cores)
| Signal | Dir | Width | Notes |
|--------|-----|-------|-------|
| `a`, `b` | in | 16 | bf16 operands |
| `y` | out | 16 | bf16 result (combinational) |

## Run the testbenches (cocotb + Verilator)
```bash
cd projects/hapicore/rtl/tb
./run_sim.sh CORE=mul    # bf16 multiplier
./run_sim.sh CORE=add    # bf16 adder
```
`run_sim.sh` forces a single consistent Python (handles conda-cocotb vs
system-verilator). Both are verified **bit-exact** against the Python golden
(`golden/hapi_fpu.py`, RNE-correct vs numpy): the multiplier over 576 directed
corners + 6,000 random + 512 subnormal/overflow edges; the adder over 625 corners
+ 6,000 random + ~5,954 cancellation/signed-zero + 392 subnormal/overflow edges.
NaN results are compared by class (payload bits are not architectural); the sign of
zero **is** checked.

## Status
- ✅ Phase 2: bf16 multiplier RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: bf16 adder RTL + cocotb
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
