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

`hapi_fp32_fma.sv` — single-cycle **fused** multiply-add `y = round(a*b + c)` with a
*single* final rounding (the true ML MAC primitive, not mul-then-add). The exact
48-bit product and 24-bit addend are aligned by their true exponents into a **128-bit
window** anchored at the larger operand's MSB — wide enough to hold the entire
rounding-relevant range exactly (full product width + cancellation headroom + guard);
bits that fall past the window (only when one operand is too small to reach the round
bit) are OR-collected into a single sticky, with a sticky-borrow on effective
subtraction. One leading-one normalise (for-loop priority encoder) + RNE; subnormal
in/out, overflow → Inf, underflow → signed zero, and fused specials (`0·Inf → NaN`,
`Inf + (−Inf) → NaN`, signed-zero). Bit-exact against the single-rounded golden
(`fp_fma`, which rounds the exact rational `a*b+c` once) — 190k+ FMAs verified.

`hapi_fma_core.sv` — the **parameterized** version of that same FMA datapath
(`EXP_W`/`MANT_W`/`BIAS`/`W`), with thin wrappers **`hapi_bf16_fma`** and
**`hapi_fp16_fma`** (both `W=48`). One core, three formats; each wrapper is bit-exact
against the single-rounded golden (150k+ FMAs each); full-ABC Yosys gives 0 latches
at bf16 ~2961 / fp16 ~3411 gates. (Their cocotb runs in CI; like fp32 the FMA
*synth* is skipped under CI — the apt Yosys there OOMs on the FMA priority-encoder
cloud even for the small cores — with the committed `.stat` as evidence.) FMA is
now complete across bf16/fp16/fp32.

`hapi_fp32_div.sv` — single-cycle **correctly-rounded** fp32 divide. Both
significands are normalised to `[2²³, 2²⁴)` (subnormals via a 24-bit CLZ), then one
exact integer division of a 51-bit dividend (`Sa << 27`) by the 24-bit divisor
yields 24 significand bits + guard, with the **division remainder** as the exact
sticky bit. The normalise-and-round tail is the FMA's magnitude round (RNE,
subnormal/underflow, overflow → Inf, `x/0 → Inf`, `0/0` & `Inf/Inf → NaN`). Bit-exact
vs `golden.fp_div` (exact rational `a/b`, one rounding) — 165k+ divisions verified.
(Its `$div`/`$mod` expand to a ~41K-gate divider, so like the FMAs the *synth* is
CI-skipped; coarse 0-latch `.stat` is committed.)

`hapi_fp32_sqrt.sv` — single-cycle **correctly-rounded** fp32 square root. Every
fp32 sqrt result is a *normal* number (√ of the smallest subnormal ≈ 2⁻⁷⁴·⁵, √ of
the max ≈ 2⁶⁴), so there is no subnormal/overflow handling. Normalize `x = M·2ᴳ`,
pick radicand `F = M` (G even) or `2M` (G odd) so the exponent is even, then one
exact **unrolled bit-by-bit integer sqrt** of `F << 28` gives 24 significand bits +
guard, with the sqrt **remainder** as the exact sticky. Same magnitude round (RNE).
Bit-exact vs `golden.fp_sqrt` (exact `math.isqrt` intermediate) — 210k+ roots
verified (incl. perfect squares). (~27K gates, synth CI-skipped like div/fma.)

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
./run_sim.sh CORE=fp32fma    # fp32 fused multiply-add
./run_sim.sh CORE=bf16fma    # bf16 fused multiply-add (hapi_fma_core)
./run_sim.sh CORE=fp16fma    # fp16 fused multiply-add (hapi_fma_core)
./run_sim.sh CORE=fp32div    # fp32 correctly-rounded divide
./run_sim.sh CORE=fp32sqrt   # fp32 correctly-rounded square root
```
`run_sim.sh` forces a single consistent Python (handles conda-cocotb vs
system-verilator). All four are verified **bit-exact** against the Python golden /
numpy fp32 (RNE-correct): bf16 mul over 576 corners + 6,000 random + 512 edges; bf16
add over 625 + 6,000 + ~5,954 cancellation + 392 edges; fp32 mul over 576 + 40,000 +
512 edges; fp32 add over 576 + 40,000 + ~29,744 cancellation + 392 edges. NaN results
compared by class (payload bits are not architectural); the sign of zero **is** checked.

## Status
- ✅ Phase 2: fp16 + bf16 + fp32 multiplier RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: fp16 + bf16 + fp32 adder RTL + cocotb
- ✅ Phase 2: **fused** multiply-add across all 3 formats — `hapi_fp32_fma` + parameterized
  `hapi_fma_core` wrappers `hapi_bf16_fma`/`hapi_fp16_fma`, each cocotb bit-exact
- ✅ Phase 2: fp32 **correctly-rounded divide** (`hapi_fp32_div`) + cocotb — 165K+ verified
- ✅ Phase 2: fp32 **correctly-rounded sqrt** (`hapi_fp32_sqrt`) + cocotb — 210K+ verified
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
- ⬜ Next: ASAP7 tech-mapping + P&R (Phase 4)
