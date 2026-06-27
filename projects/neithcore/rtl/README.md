# NeithCore RTL (Phase 2)

Combinational arithmetic primitives of the lattice-KEM number-theoretic transform,
all over the golden's NTT-friendly prime **Q = 7681** (residues in `[0, Q)`).

`neith_modmul.sv` — single-cycle modular multiplier `(a*b) mod 7681` via **Barrett
reduction**. The product `P = a*b < 2^26`; with `mu = floor(2^26/Q) = 8736` the
quotient estimate `floor(P*mu / 2^26)` is within 2 of the truth, so a small fixed
number of conditional `−Q` subtractions restores the canonical residue. No divider.

`neith_butterfly.sv` — single-cycle radix-2 **Cooley-Tukey butterfly** (the atom of
`golden.ntt_cyclic`): `t = v*w mod Q`, `lo = (u+t) mod Q`, `hi = (u−t) mod Q`. It
instantiates `neith_modmul` for the twiddle multiply and does the mod add/sub with
single conditional subtractions.

`neith_ntt.sv` — the **multicycle 256-point NTT engine**, forward **and** inverse. An
FSM streams 256 coefficients in (each stored at its **bit-reversed** index), then runs
8 radix-2 stages × 128 in-place butterflies (one `neith_butterfly` per cycle, ~1024
cycles), with the twiddle `w` advanced by a second `neith_modmul` (`w *= wlen`, reset
to 1 at each block; `wlen` is a per-stage ROM). `mode` (latched at `start`) selects
forward (`root = OMEGA`, matches `golden.ntt_cyclic(a, OMEGA)`) or inverse
(`root = OMEGA_INV` + a final `×N_INV` scaling pass, matching
`ntt_cyclic(A, OMEGA_INV)·N_INV`). Results are read out by address.

## Interfaces
| Module | Inputs | Outputs |
|--------|--------|---------|
| `neith_modmul`   | `a[12:0]`, `b[12:0]` | `r[12:0]` = `(a·b) mod Q` |
| `neith_butterfly`| `u[12:0]`, `v[12:0]`, `w[12:0]` | `lo` = `(u+v·w) mod Q`, `hi` = `(u−v·w) mod Q` |
| `neith_ntt`      | `clk,rst_n,start,mode,in_valid,in_data[12:0],rd_addr[7:0]` | `out_data[12:0]`, `busy`, `done` |

## Run the testbenches (cocotb + Verilator)
```bash
cd projects/neithcore/rtl/tb
./run_sim.sh CORE=modmul       # modular multiplier
./run_sim.sh CORE=butterfly    # CT butterfly (+ modmul)
./run_sim.sh CORE=ntt          # 256-point engine (+ butterfly + modmul)
```
All verified **bit-exact** vs the Python golden (`golden/neith_mlkem.py`):
`neith_modmul` over 121 corners + 30,000 random + 1,600 near-modulus worst cases;
`neith_butterfly` over 729 corners + 30,000 random + 2,048 real-`OMEGA^k`-twiddle
butterflies; `neith_ntt` over directed vectors + 16 random **forward** + 16 random
**inverse** transforms vs `golden.ntt_cyclic`, plus 12 forward→inverse **roundtrips**
that recover the original input.

## Status
- ✅ Phase 2: modular multiplier + CT butterfly RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: 256-point NTT engine RTL (forward + inverse + 1/N scale) + cocotb
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
- ⬜ Next: psi pre/post-multiply for the full negacyclic `ntt()`/`intt()`, SRAM macro, then ASAP7
