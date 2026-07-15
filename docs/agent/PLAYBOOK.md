# PLAYBOOK — Every Step, With Exact Commands

This is the full procedure. `AGENTS.md` is the summary; this file is the ground
truth. Do not improvise a different flow.

---

## Part A — Toolchain (exact paths on this machine)

These binaries are NOT all on `PATH`. Use the full paths.

| Tool | Path / command | Used for |
|------|----------------|----------|
| Python tests | `pytest projects/ -q` | Phase 0/1 golden + pymodel |
| Verilator | `/usr/bin/verilator` (on PATH as `verilator`) | cocotb RTL sim |
| cocotb | conda base env, Python 3.13 (already installed) | RTL testbenches |
| Yosys | `~/miniconda3/envs/eda/bin/yosys` | synthesis / 0-latch check |
| yosys-smtbmc | `~/miniconda3/envs/eda/bin/yosys-smtbmc` | formal BMC / k-induction |
| z3 | `~/miniconda3/bin/z3` | SMT solver for smtbmc (`-s z3`) |
| Docker + ORFS | `docker`, image `openroad/orfs:latest` (already pulled) | Phase 4 P&R → GDSII |

You never call these raw for the common path — each core wraps them:

```bash
# Phase 0/1 — golden + pymodel (fast, <0.5 GB RAM, never OOMs)
pytest projects/ -q
pytest projects/<core>/tests -v          # one core

# Phase 2 — RTL cocotb, bit-exact vs golden (this is the PASS/FAIL you need)
./projects/<core>/rtl/tb/run_sim.sh CORE=<modulename>

# Phase 3 — Yosys synth, must assert 0 latches
./projects/<core>/synth/run_synth.sh

# Phase 5 — formal (only cores that have a formal/ dir)
./projects/<core>/formal/run_formal.sh

# Phase 4 — ASAP7 7nm P&R → routed GDSII (Docker; ~10 min small block)
flow/harden.sh <designname>              # LEC_CHECK=0 is baked in — do not remove it

# Regenerate ALL tracking docs from tools/manifest.py (do after any status change)
python tools/gen_tracking.py
```

`tools/manifest.py` is the **single source of truth** for status and checkpoints.
You edit `manifest.py`, then run `gen_tracking.py`, which rewrites `PROGRESS.md`
and every `projects/<core>/{STEPS,CHECKPOINTS,TESTS}.md`. **Never hand-edit those
generated files** — your edit will be overwritten.

---

## Part B — The per-task loop, step by step

### Step 1 — Orient (every session)
```bash
cd /home/lordegypt/KemetCore
git status                 # must be clean (only scratchpad/ untracked is OK)
git checkout main && git pull
pytest projects/ -q        # MUST be green. If red, STOP and log it — do not build on red.
```
Read `docs/agent/RESUME.md` FIRST (current state + exact next step), then
`PROGRESS.md`, then the tail of `docs/agent/WORKLOG.md` to see what the previous
session did and whether anything is half-finished.

### Step 12 — Save your place (end of EVERY session)
Overwrite `docs/agent/RESUME.md` so the next "continue kemetcore" resumes instantly:
```bash
# edit docs/agent/RESUME.md: update "Current state" + "NEXT STEP" to reflect NOW
git add docs/agent/RESUME.md
git commit -m "docs(agent): update RESUME state" && git push
```
Also refresh your Antigravity memory (AGENTS.md §7): *"KemetCore → open the repo,
read docs/agent/RESUME.md, follow AGENTS.md, Gemini 3 Pro High, never self-merge."*

### Step 2 — Pick ONE small task
From `docs/agent/TASK_MENU.md`, or the specific thing Mohamed asked for. Scope =
one RTL module, or one formal proof, or one P&R block. If a task feels like it
touches 5 files across 3 cores, it is too big — split it.

### Step 3 — Branch
```bash
git checkout -b feat/<core>-<short-thing>     # e.g. feat/neithcore-poly-add
```

### Step 4 — Read before writing
Open, in this order:
- the golden model for the core (`projects/<core>/*.py`) — this is the spec.
- the existing RTL in `projects/<core>/rtl/` — copy its naming, reset style, idiom.
- the test harness `projects/<core>/rtl/tb/` — you will add a testbench like these.
Never write RTL for a function whose golden reference you have not read.

### Step 5 — Build the smallest correct thing
- Match surrounding style exactly (comment density, signal naming, `always_comb`
  vs `always_ff`, reset convention).
- No stubs, no dead code, no speculative features, no "cleanup" of unrelated code.
- If you add a testbench, mirror an existing one in the same core.

### Step 6 — Verify locally (all applicable gates, all green)
```bash
./projects/<core>/rtl/tb/run_sim.sh CORE=<x>     # bit-exact vs golden — READ the output
./projects/<core>/synth/run_synth.sh             # confirm "0 latches" / "$_DLATCH_ = 0"
./projects/<core>/formal/run_formal.sh           # if a proof is involved — must print PASSED
pytest projects/<core>/tests -q                  # if you touched golden/pymodel
```
If any gate fails, fix the **root cause** — do not patch the symptom, do not weaken
the test to make it pass. A failing bit-exact check means your RTL disagrees with
the spec; find out where.

### Step 7 — Update status + regenerate tracking
If you completed a checkpoint, edit `tools/manifest.py` (add the checkpoint tuple,
or flip a phase from `todo`→`partial` / `partial`→`done` — **only if it is
genuinely that state**; `partial` ≠ `done`). Then:
```bash
python tools/gen_tracking.py
```

### Step 8 — Save (commit + log) — DO THIS EVERY STEP
```bash
git add -A
git commit -m "feat(<scope>): <what> — <how verified>"     # + Co-Authored-By trailer
git push -u origin HEAD
```
Then append an entry to `docs/agent/WORKLOG.md` (format at top of that file).

### Step 9 — Open the PR
```bash
gh pr create --title "..." --body "..."     # gh pr create WORKS
# To EDIT a PR later, gh pr edit is BROKEN here — use:
gh api --method PATCH repos/Lord1Egypt/KemetCore/pulls/<N> -f title="..." -f body="..."
```
Wait for CI. The two required checks are **"Phase 0/1 tests"** and **"Phase 2
RTL"**. Poll with `gh pr checks <N>`. Phase 2 RTL runs every core's testbench and
takes ~25 minutes — that is normal, not a hang.

### Step 10 — Stop at the gate
When CI is green, **STOP**. Post in the worklog that PR #N is green and awaiting
merge. Do **not** merge. Wait for Mohamed to say "merge".

### Step 11 — Merge (only on Mohamed's explicit word)
```bash
gh pr merge <N> --merge --delete-branch
git checkout main && git pull
```
If several PRs are open and share `tools/manifest.py` / `PROGRESS.md`, merge them
one at a time; after each merge the others are behind:
```bash
git checkout <other-branch>
git rebase origin/main
# generated-file conflicts (PROGRESS.md, CHECKPOINTS.md) resolve by REGENERATING:
git checkout --theirs PROGRESS.md projects/*/CHECKPOINTS.md ; git add -A ; git rebase --continue
python tools/gen_tracking.py
git add -A && git commit --amend --no-edit && git push --force-with-lease
```

---

## Part C — Formal proofs (the highest-risk area — read fully before writing one)

Past sessions shipped **vacuous** proofs (printed PROVED while checking zero
assertions). Do not repeat that. A proof is only real if ALL of these hold:

1. **Non-vacuous:** the emitted `.smt2` actually contains `assert`. Check it:
   `grep -c assert build/*.smt2` must be > 0.
2. **Lowered correctly:** `write_smt2` in Yosys 0.65 **drops `$check` cells** unless
   you run `async2sync` first. ALWAYS `async2sync` before `write_smt2`, even for
   combinational designs. (This was the exact root cause of the vacuity bug.)
3. **Mutation-tested:** deliberately corrupt the RTL logic → the proof must FAIL;
   restore it → the proof must PASS. If a corrupted design still "passes", the
   proof is checking nothing.
4. **Honestly labeled:** a control-safety invariant is NOT full functional
   correctness. Say what you proved and what stays cocotb-covered. Mark the phase
   `partial`, not `done`, unless it is genuinely complete.

Toolchain facts:
- Combinational property → one BMC step: `yosys-smtbmc -s z3 -t 1 x.smt2`.
- Sequential / FSM → k-induction: `prep -top X; async2sync; dffunmap; write_smt2`
  then `yosys-smtbmc -s z3 -i -t N`. Flag is `-s z3`, NOT `--solver`.
- `read_verilog` needs `-formal`. `$past()` works in yosys 0.65.
- Yosys 0.65 has **no `bind` and no hierarchical refs** — embed asserts INSIDE the
  RTL under `` `ifdef FORMAL `` (compiled only with `-DFORMAL`, invisible to
  cocotb/synth). After doing so, re-run cocotb + synth to prove they still pass
  (the guard keeps them inert).
- **z3 CANNOT converge** on: fp32-adder equivalence miters, divider equivalence
  miters, Barrett-modulo-vs-`%` equivalence. Do not attempt these — pick a
  tractable property instead (fp32-MUL commutativity DOES converge; output-range
  and identity properties converge fast).
- SYNC-reset designs: plain BMC-from-reset spuriously fails (t=0 flops
  unconstrained) → use k-induction `-i`.
- Grep the smtbmc result on the exact string `"Status: PASSED"`, not bare
  `"PASSED"` (a counterexample trace can contain that word).

---

## Part D — Phase 4 P&R (Docker ORFS) specifics

- `flow/harden.sh <design>` runs ASAP7 7nm through synth→place→CTS→route→GDS in the
  `openroad/orfs:latest` container. `LEC_CHECK=0` is baked in — it skips only an
  optional AVX-512 formal check that SIGILLs on this Coffee-Lake CPU; the physical
  flow is unaffected. Do not remove it.
- Add a new block: copy `flow/designs/asap7/<existing>/`, point `config.mk`
  `VERILOG_FILES` at your RTL + deps, set the clock in `constraint.sdc`, run
  `flow/harden.sh <name>`. Commit only `config.mk` + `constraint.sdc` (the `.gds`
  is gitignored). `flow/gen_harden_results.py` rebuilds `flow/HARDEN_RESULTS.md`
  from the real reports — never hand-type WNS/area numbers.
- ORFS runs as root: clean stale results via the container, not host `rm`:
  `docker run --rm -v $PWD:/work openroad/orfs rm -rf flow/{results,logs,reports,objects}/asap7/<d>`.
- Small/medium blocks close on this 12 GB laptop (~1.85 GB peak). Large flat
  designs (PtahConv ~3 mm², big arrays, full CPU with flat memory-as-flops) hit a
  hold-buffer / RAM wall and need an SRAM-macro / hierarchical flow or a bigger box
  — do NOT commit a design that does not close timing (WNS must be ≥ 0).

---

## Part E — If a background job (merge train / CI waiter) is running

- Launch waiters with the agent's background mechanism, and have them poll PR
  state via `gh pr view <N> --json state -q .state == "MERGED"` — do NOT detect
  merge by grepping `gh pr merge` stdout (unreliable).
- While a background job may `git checkout main`, do NOT start new work in the same
  working tree. Use a `git worktree` for parallel work, or wait for the job to
  finish and branch off fresh `main`.
