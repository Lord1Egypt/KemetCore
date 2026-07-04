# KemetCore — Phase 4 (P&R → GDSII) flow

KemetCore blocks are hardened on the **ASAP7 7 nm** predictive PDK through the
[OpenROAD-Flow-Scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
container (`openroad/orfs:latest`) — the same flow the sibling PtahCore project uses.

## Run

```bash
flow/harden.sh bast_mac        # synth → floorplan → place → CTS → route → GDS
```

Needs Docker + the `openroad/orfs:latest` image (ASAP7 PDK is bundled inside).
A design is just `flow/designs/asap7/<name>/{config.mk,constraint.sdc}` pointing
at the RTL (see `bast_mac` for the template). Results land under
`flow/results/asap7/<name>/base/` (git-ignored).

## Status (this machine: i7-9750H, 12 GB, WSL2)

`bast_mac` (BF16 MAC PE) runs cleanly through **synthesis, floorplan and
placement** on ASAP7:

| metric | value |
|--------|-------|
| design area | **637 µm²** |
| utilisation | 45.6 % |
| instances | ~6,483 std cells |
| peak RAM | ~0.26 GB |

**CTS blocker on this CPU:** clock-tree synthesis aborts with
`child killed: illegal instruction`. The container correctly sees the host CPU
flags (avx2/fma/bmi2 — Coffee Lake has **no AVX-512**) and base `openroad` runs,
but a narrow TritonCTS sink-clustering code path in the prebuilt binary uses an
instruction this CPU lacks (`SIGILL`). This is **not** a design, RTL, or RAM
issue — placement (the RAM-heavy part for small blocks) completes with room to
spare.

### How to get a full GDSII

1. **Compatible / cloud runner** — run `flow/harden.sh` on a box with an AVX-512
   CPU or a portable OpenROAD build. This is how PtahCore produced its GDS
   (`ptahcore/CLOUD_HANDOFF.md`). Small KemetCore blocks close in minutes.
2. **From-source OpenROAD** built for this CPU (`-march=native`) — definitive but
   heavy to build locally.
3. **RAM** is the only *hardware* wall, and only for *large* flat designs
   (PtahConv ~3 mm², tiled arrays, RaCore) which peak >12 GB in detailed route —
   small/medium blocks are fine here once the CTS/CPU issue is resolved.

The flow, configs and constraints are committed and repeatable; only the CTS
binary/CPU mismatch stands between this laptop and a full local GDSII.
