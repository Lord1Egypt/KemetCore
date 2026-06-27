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

## Interfaces
| Module | Inputs | Outputs |
|--------|--------|---------|
| `neith_modmul`   | `a[12:0]`, `b[12:0]` | `r[12:0]` = `(a·b) mod Q` |
| `neith_butterfly`| `u[12:0]`, `v[12:0]`, `w[12:0]` | `lo[12:0]` = `(u+v·w) mod Q`, `hi[12:0]` = `(u−v·w) mod Q` |

## Run the testbenches (cocotb + Verilator)
```bash
cd projects/neithcore/rtl/tb
./run_sim.sh CORE=modmul       # modular multiplier
./run_sim.sh CORE=butterfly    # CT butterfly (+ modmul)
```
Both verified **bit-exact** vs the Python golden (`golden/neith_mlkem.py`):
`neith_modmul` over 121 corners + 30,000 random + 1,600 near-modulus worst cases;
`neith_butterfly` over 729 corners + 30,000 random + 2,048 real-`OMEGA^k`-twiddle
butterflies.

## Status
- ✅ Phase 2: modular multiplier RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: CT butterfly RTL + cocotb
- ✅ Phase 3: Yosys synthesis (gate count + 0-latch check) — see `../synth/`
- ⬜ Next: multicycle 256-point NTT engine (twiddle ROM + ping-pong RAM), then ASAP7
