# TASK MENU — What To Work On Next

Pick ONE item per PR. Prefer the tractable, verifiable ones. When Mohamed gives a
specific task, that overrides this menu. Update this file (add/strike items) as the
state moves, and always regenerate `PROGRESS.md` after any manifest change.

## Current state (as of the handoff)
- All 11 cores: Phase 0/1 (golden + pymodel) ✅, Phase 2/3 (RTL + Yosys 0-latch) 🔧,
  Phase 4 (7nm GDSII on a representative block per core) 🔧, Phase 5 (formal) 🔧.
- Overall strict tracker: **34% (23/66 slots)** — honest; `partial` doesn't count.
- `main` is clean, no open PRs. `pytest projects/ -q` is green.

## Good next levers (tractable, high-confidence — start here)

1. **More Phase-2 RTL breadth.** Any core has golden functions without RTL yet, or
   RTL modules without a cocotb testbench. Pick one small module, build it
   bit-exact vs its golden, prove 0-latch. This is the safest, most repeatable win.
   Good candidates historically: additional NeithCore poly ops, AtumCore vector
   ops, SobekCore ray-math primitives, HapiCore FPU corners.

2. **More Phase-4 P&R breadth.** Harden another per-core block toward "full-core P4".
   Copy an existing `flow/designs/asap7/<block>/`, point it at new RTL, close timing
   at a realistic clock, commit config + SDC only. Small/medium blocks only (they
   close on this laptop). See PLAYBOOK Part D.

3. **Formal proofs — LOWEST priority, and mostly SATURATED.** Prefer options 1 and 2
   above. Only touch formal if you are adding a *genuinely new, deeper* property to a
   core, with a NEW proof file or NEW `` `ifdef FORMAL `` asserts — non-vacuous and
   mutation-tested. AVOID intractable miters (fp32-adder / divider / Barrett-modulo —
   z3 never converges). **⛔ Do NOT re-run an existing proof and flip its checkpoint
   `partial`→`done` — that is tracker inflation and will be rejected in review.** The
   existing combinational proofs are deliberately `partial` (a single algebraic
   property ≠ full functional signoff); leave them `partial` unless you actually
   prove full functional equivalence.

## Bigger levers (higher effort / may be gated — discuss with Mohamed first)

4. **Full-core GDSII** (a whole core, not just a block). Blocked by the flat
   memory-as-flops hold-buffer explosion; needs an SRAM-macro or hierarchical CTS
   flow. Do not force a non-closing design. This is a real research task — log a
   plan before starting.

5. **SethCore pipeline the Zicsr core.** The single-cycle RV32IMZicsr core
   (`seth_core_csr`) is complete; pipelining it means adding `op==7'h73` to
   `id_uses_rs1`, splitting ecall/CSR by funct12, and trap-flush. Verify vs the
   `CpuZ` golden.

6. [x] **RaCore (Top-Level SoC) - NoC Interconnect & Integration**
   * Implemented `ra_noc_xbar` and successfully integrated `racore_lite` inside phase 2 RTL. 
   * Waiting on further external components/cores before full `racore` can be complete.

7. **Timing/SDC discipline** across cores (real clock targets, not just gate counts).

## Formal breadth status — SATURATED (do not redo)
Formal proofs already exist for every core that has a tractable property, and each
combinational core already has its proof file: `formal_bias_relu.sv` (PtahConv),
`formal_mask.sv` (ImentetCore), `formal_scale.sv` (SobekCore), `formal_int8_mac.sv`
(BastCore), `formal_prune.sv` (GebCore), plus HapiCore/NeithCore/SethCore/AtumCore.
Every FSM core has a sequential k-induction proof. **There is essentially no new
formal work to pick up** — do NOT re-run these and do NOT flip their `partial`
checkpoints to `done`. **Default to Phase-2 RTL breadth (option 1) or Phase-4 P&R
breadth (option 2).** Those are where real, non-duplicate progress lives.

## Rule for every item
One small PR, all gates green, tracking regenerated, worklog updated, then wait for
merge. Honest labels — `partial` until genuinely complete.
