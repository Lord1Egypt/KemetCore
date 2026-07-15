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

3. **Deepen a formal proof where z3 stays tractable.** Add a genuine, non-vacuous,
   mutation-tested property to a core that only has a shallow one. AVOID the
   intractable miters (fp32-adder / divider / Barrett-modulo equivalence — z3 never
   converges). Range, identity, commutativity-of-mul, and FSM control-safety
   invariants all converge fast. See PLAYBOOK Part C.

## Bigger levers (higher effort / may be gated — discuss with Mohamed first)

4. **Full-core GDSII** (a whole core, not just a block). Blocked by the flat
   memory-as-flops hold-buffer explosion; needs an SRAM-macro or hierarchical CTS
   flow. Do not force a non-closing design. This is a real research task — log a
   plan before starting.

5. **SethCore pipeline the Zicsr core.** The single-cycle RV32IMZicsr core
   (`seth_core_csr`) is complete; pipelining it means adding `op==7'h73` to
   `id_uses_rs1`, splitting ecall/CSR by funct12, and trap-flush. Verify vs the
   `CpuZ` golden.

6. **RaCore SoC integration** — wire multiple accelerators behind the KAI interface.
   Largest scope; capstone. Plan explicitly first.

7. **Timing/SDC discipline** across cores (real clock targets, not just gate counts).

## Formal breadth status (so you don't redo saturated work)
Every core WITH a real control FSM already has a sequential proof (RaCore arbiter,
SethCore muldiv_seq, BastCore int8_mac, AnubisCore sha256, NeithCore ntt, PtahConv
conv2d, AtumCore vcore). The remaining combinational-only cores (SobekCore,
ImentetCore, GebCore, HapiCore) have no FSM to prove — deepen their datapath
properties instead, don't invent an FSM.

## Rule for every item
One small PR, all gates green, tracking regenerated, worklog updated, then wait for
merge. Honest labels — `partial` until genuinely complete.
