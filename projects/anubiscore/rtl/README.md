# AnubisCore RTL (Phase 2)

`sha256_core.sv` — synthesizable SHA-256 core. Multicycle: 1 round/cycle, 64 rounds
per 512-bit block, 16-word sliding-window message schedule, `init`/continue chaining
for multi-block messages.

## Interface
| Signal | Dir | Width | Notes |
|--------|-----|-------|-------|
| `clk`, `rst_n` | in | 1 | active-low async reset |
| `start` | in | 1 | pulse 1 cycle to absorb a block |
| `init` | in | 1 | 1 = first block (use IV), 0 = chain |
| `block` | in | 512 | padded block, W0 = most-significant 32 bits |
| `busy` / `done` | out | 1 | `done` pulses when the block is absorbed |
| `hash` | out | 256 | `{H0..H7}`, valid the cycle after `done` |

`sha3_256_core.sv` — synthesizable SHA3-256 (Keccak-f[1600]): absorb 1088-bit rate
blocks, 24-round permutation (1 round/cycle), `init`/chain; digest = first 4 state
lanes. Host pre-packs each rate lane little-endian.

## Run the testbenches (cocotb + Verilator)
```bash
cd projects/anubiscore/rtl/tb
./run_sim.sh CORE=sha256    # SHA-256
./run_sim.sh CORE=sha3      # SHA3-256 / Keccak
```
`run_sim.sh` forces a single consistent Python (handles conda-cocotb vs system-verilator).
Both verified bit-exact against the Python golden + hashlib on 9 messages each
(empty, "abc", block-boundary lengths, multi-block, random).

## Status
- ✅ Phase 2: SHA-256 RTL + cocotb (Verilator 5.020)
- ✅ Phase 2: SHA3-256 / Keccak-f[1600] RTL + cocotb
- ⬜ Phase 3 Yosys synthesis (gate count + 0-latch check)
