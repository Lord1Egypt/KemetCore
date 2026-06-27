# BastCore RTL (Phase 2)

`bast_mac.sv` — the processing element (PE) of the BF16 tensor core: a
**bf16-multiply / fp32-accumulate** MAC. Each cycle it multiplies a bf16 pair,
widens the bf16 product to fp32 (an *exact* zero-extend — bf16 and fp32 share the
8-bit, bias-127 exponent field), and accumulates into a registered fp32 sum. This
is exactly the golden datapath `out = Σ_k round_bf16(a_k·b_k)` accumulated in fp32
(`golden/bast_matmul.py`).

It composes the verified HapiCore primitives **`hapi_bf16_mul`** + **`hapi_fp32_add`**
(merged from PRs #3 and #5) — so the tensor core inherits their bit-exact rounding.

## Interface
| Signal | Dir | Width | Notes |
|--------|-----|-------|-------|
| `clk`, `rst_n` | in | 1 | active-low async reset |
| `en` | in | 1 | accumulate the `(a,b)` product this cycle |
| `clear` | in | 1 | start a fresh dot product (seed accumulator with +0) |
| `a`, `b` | in | 16 | bf16 operands |
| `acc` | out | 32 | fp32 running accumulator (registered) |

Drive a length-K dot product by pulsing `clear` with the first element and holding
`en` for all K cycles; `acc` is valid one cycle after the last input.

## Run the testbench (cocotb + Verilator)
```bash
cd projects/bastcore/rtl/tb
./run_sim.sh CORE=mac
```
Verified **bit-exact** against `golden.matmul` on 400 random `(1×K)·(K×1)` dot
products (K = 1..24), including wild bf16 inputs that exercise rounding,
cancellation, and the fp32 accumulate.

## Status
- ✅ Phase 2: MAC cell RTL (bf16 mul + fp32 accumulate) + cocotb (Verilator 5.020)
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
- ⬜ Next: 16×16 `mac_grid` systolic array, then ASAP7 tile-abutment + P&R
