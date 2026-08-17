# 𓋹 Post-100% Goal — Real Fab PDK Target

> **Gate:** Do not start this until `PROGRESS.md` shows 100% (all 11 cores through Phase 5 signoff on ASAP7). This document is the plan for what comes *after*, not a parallel track.

## Why

Everything shipped so far targets **ASAP7**, a predictive 7nm academic PDK — it proves the methodology (golden → pymodel → RTL → cocotb → Yosys → OpenROAD) but produces GDSII that cannot be sent to any real fab. The next milestone is retargeting to a PDK that can actually be manufactured, so KemetCore's silicon claims stand on the same ground as comparable projects (OpenTitan, Ibex, black-parrot, serv, VeeR-EL2) that have real tapeouts.

## Target PDK: sky130

Chosen over gf180mcu and IHP sg13g2 because:
- **Most precedent** — black-parrot, serv, and VeeR-EL2 all taped out on sky130; largest body of prior art and community troubleshooting.
- **Toolchain already supports it** — OpenROAD-flow-scripts ships a `sky130hd` platform config out of the box, including a reference `ibex` design at `flow/designs/sky130hd/ibex/config.mk`, the closest public analog to SethCore.
- **Live path to real silicon exists (as of 2026):** ChipFoundry (ex-Efabless team) runs sky130 MPW shuttles at SkyWater; Cadence has also run a sky130 shuttle. (Verify current shuttle cadence/cost/queue before committing — this landscape shifts; Efabless itself shut down in March 2025.)

## What carries over vs. what doesn't

**Mechanical (config swap):**
- Toolchain stays Yosys + OpenROAD-flow-scripts — swap `PLATFORM=asap7` → `PLATFORM=sky130hd` per core, retune floorplan/utilization.
- DRC/LVS moves to Magic + Netgen with real sky130 rule decks.

**Real engineering work:**
- **Area re-derivation.** ASAP7 areas/gate-counts in the project comparison matrix don't map to any real process — recompute per core against real sky130 std-cell (`sky130_fd_sc_hd`) areas. Expect a large increase; some ML accelerators may need smaller array dimensions to fit a realistic shuttle die/area cap.
- **Fmax retargeting.** Current targets (500MHz–1GHz for AnubisCore) assume 7nm-predictive timing. Realistic sky130 targets are typically 50–150MHz — redo constraints against real liberty files.
- **Memory macros.** Any generated SRAM (e.g. RaCore's scratchpad) needs regenerating for sky130 (OpenRAM or similar) — ASAP7 memory compilers don't carry over.
- **DFT.** Scan chain insertion — currently absent per README's own "what it is not" section; becomes mandatory for a real submission.
- **CDC.** Synchronizers on any core with external-facing async interfaces — also currently absent.
- **Padring/harness.** Wrap the target core in a real IO harness (e.g. a Caravel-style or ChipFoundry harness) instead of standing alone as a macro.
- **Full-corner signoff.** Multi-corner STA, IR drop, electromigration — a higher bar than the PoC-level "DRC clean" from ORFS today.

## Sequencing

Do **not** retarget all 11 cores at once. Every comparable project that actually taped out proved one small core end-to-end first.

1. Pick the smallest/cheapest core as the pathfinder — **AnubisCore** (smallest gate count, ~15K gates / ~0.05mm² at ASAP7 scale) is the candidate.
2. Take just that core through: sky130hd synth/P&R via ORFS → area/Fmax re-derivation → DFT + CDC → Magic/Netgen signoff → harness integration.
3. Everything learned (area budgeting, realistic Fmax, DFT/CDC patterns, harness integration) becomes the template for the remaining ten cores.
4. Only after the pathfinder core is a clean, submittable design, decide whether to retarget the rest of the portfolio or select a subset for an actual shuttle submission.

## Definition of done for this phase

- [ ] PDK choice confirmed (sky130 vs. alternatives) after checking current shuttle availability/cost
- [ ] Pathfinder core (AnubisCore) resynthesized and placed-and-routed on sky130hd via ORFS
- [ ] Real DRC/LVS clean via Magic + Netgen against sky130 rule decks (not ORFS's internal checks)
- [ ] DFT scan chains added and verified
- [ ] CDC synchronizers added on external-facing interfaces
- [ ] Core integrated into a real IO harness
- [ ] Multi-corner STA + power signoff (IR drop, EM) passing
- [ ] Go/no-go decision recorded on whether to submit to an actual MPW shuttle
