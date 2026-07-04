# KemetCore — Phase 4 (P&R → GDSII) flow

KemetCore blocks are hardened to **GDSII** on the **ASAP7 7 nm** predictive PDK
through the [OpenROAD-Flow-Scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
container (`openroad/orfs:latest`) — the same flow the sibling PtahCore project uses.

## Run

```bash
flow/harden.sh bast_mac        # synth → floorplan → place → CTS → route → GDS
```

Needs Docker + the `openroad/orfs:latest` image (ASAP7 PDK is bundled inside).
A design is just `flow/designs/asap7/<name>/{config.mk,constraint.sdc}` pointing
at the RTL (see `bast_mac` for the template). Results land under
`flow/results/asap7/<name>/base/6_final.gds` (git-ignored).

## Status — WORKS end-to-end locally ✅

`bast_mac` (BF16 MAC PE) hardens all the way to a **routed, DRC-clean GDSII on
ASAP7 7 nm, on this laptop** (i7-9750H, 12 GB, WSL2):

| metric | value |
|--------|-------|
| GDSII | `6_final.gds` (~7.8 MB) |
| design area | ~647 µm² @ 46% utilisation |
| antenna DRC | 0 net / 0 pin violations |
| peak RAM | ~1.85 GB |
| wall time | ~10 min (NUM_CORES=4) |

### The one fix that was needed: `LEC_CHECK=0`

Out of the box, CTS aborted with `child killed: illegal instruction`. Root cause:
ORFS runs a post-resize **logical-equivalence check** (`run_lec_test`) that execs
the image's bundled formal binary (`KEPLER_FORMAL_EXE`), which is compiled with
**AVX-512** — an instruction set this Coffee Lake CPU lacks (it has avx2/fma/bmi2,
and base `openroad` runs fine). Setting **`LEC_CHECK=0`** skips only that optional
equivalence check; the entire physical flow (synth→place→CTS→route→GDS) is
unaffected. This is now baked into `flow/harden.sh`.

## Notes / knobs

- **Timing:** `bast_mac` does bf16-mul → widen → fp32-add → register in one
  combinational cycle (~3.4 ns critical path), so `constraint.sdc` uses a 250 MHz
  (4 ns) clock to close. A faster target needs a pipelined MAC.
- **RAM ceiling (the only *hardware* limit):** small/medium blocks fit easily.
  Only *large flat* designs — PtahConv ~3 mm², tiled arrays, RaCore SoC — peak
  >12 GB in detailed route and need a ≥24 GB box (or tile-abutment).
- **Bringing a new block to GDS:** copy `designs/asap7/bast_mac/`, point
  `VERILOG_FILES` at the new RTL + its deps, set a clock in `constraint.sdc`,
  then `flow/harden.sh <name>`.
