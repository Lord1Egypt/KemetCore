# AGENTS.md — Operating Contract for AI Coding Agents (Antigravity / Gemini)

> **This file is loaded automatically by Antigravity, Gemini CLI, and most agent
> tools.** It is the single entry point. Read it fully before you touch anything.
> The deep, step-by-step playbook lives in [`docs/agent/`](docs/agent/). You MUST
> read [`docs/agent/PLAYBOOK.md`](docs/agent/PLAYBOOK.md) and
> [`docs/agent/AVOID_LIST.md`](docs/agent/AVOID_LIST.md) before your first change.

You are continuing **KemetCore**, an open-source silicon lab: 11 hardware
accelerators, each carried through the flow
`golden model → pymodel → SystemVerilog RTL → cocotb → Yosys synth → OpenROAD P&R → 7nm GDSII → formal signoff`.
The owner is **Mohamed (Lord1Egypt)**. He trusts careful, honest, tested work and
will periodically review what you did and rate it. Your job is to make that review
easy: small, verified, well-logged steps.

---

## 0. The one rule that matters most

**Never claim something works until you have run it and seen it pass.**
"It should work" is a failed task. Every RTL change is proven bit-exact against a
golden model. Every synth run is proven 0-latch. Every formal proof is proven
non-vacuous and mutation-tested. If you cannot verify it, you do not commit it.

---

## 1. Which Gemini model to use

| Work type | Model | Why |
|-----------|-------|-----|
| **RTL design, formal proofs, debugging, git/PR reasoning, anything correctness-critical** | **Gemini 3 Pro — High thinking** | This work is deep, multi-step, and a single wrong bit fails silently. Pro-High reasons through IEEE-754 edge cases, k-induction, and hazard logic. This is your DEFAULT. |
| Mechanical polling only (waiting on CI, reading a log, re-running an existing test) | Gemini 3 Flash — High | Cheap and fast for zero-reasoning chores. Never use Flash to write RTL or a formal proof. |

**Default to Pro-High for essentially all real work.** Mohamed has a Pro plan that
is otherwise unused — spend it on correctness. Only drop to Flash for "watch this
CI run and tell me when it's green" style busywork. When in doubt, use Pro-High.

---

## 2. The core loop (every task, no exceptions)

This is the short version. The full version with exact commands is in
[`docs/agent/PLAYBOOK.md`](docs/agent/PLAYBOOK.md).

1. **Orient.** Read `PROGRESS.md`, then run `pytest projects/ -q` — it must be
   green before you start. If it is not, STOP and report; do not build on red.
2. **Pick ONE small task** from [`docs/agent/TASK_MENU.md`](docs/agent/TASK_MENU.md)
   (or the task Mohamed gave you). One module / one proof / one block at a time.
3. **Branch.** `git checkout main && git pull && git checkout -b feat/<short-name>`.
   Never commit to `main` directly — it is branch-protected and will reject you.
4. **Read before you write.** Open the golden model, the existing RTL neighbours,
   and the test harness for the core you are touching. Match their style exactly.
5. **Build the smallest thing that works.** No stubs, no `TODO: later`, no dead
   code, no features nobody asked for.
6. **Verify locally — all three gates that apply:**
   - cocotb bit-exact vs golden: `./projects/<core>/rtl/tb/run_sim.sh CORE=<x>`
   - Yosys 0-latch: `./projects/<core>/synth/run_synth.sh`
   - formal (if applicable): `./projects/<core>/formal/run_formal.sh`
   Every one must pass with exit code 0. Show yourself the output.
7. **Regenerate tracking:** `python tools/gen_tracking.py` (updates `PROGRESS.md`
   and the per-project docs from `tools/manifest.py`).
8. **Save the work** — commit immediately (see §3) AND append to the worklog (§4).
9. **Open a PR**, let CI go green, then **STOP and wait for Mohamed to say
   "merge"** (see §5 — you may not self-merge without his explicit word).
10. **Self-review** against [`docs/agent/REVIEW_CHECKLIST.md`](docs/agent/REVIEW_CHECKLIST.md)
    before you call anything done.

---

## 3. Save after every step — commit discipline

**Commit the moment a step verifies green. Do not batch. Do not leave work
uncommitted.** A crashed session with committed work loses nothing; a crashed
session with a dirty tree loses everything.

- Commit message format:
  `feat(<coreORphase>): <what> — <how verified>`
  e.g. `feat(phase2): NeithCore neith_add RTL — cocotb bit-exact vs golden, Yosys 0-latch`
- End every commit body with the co-author trailer:
  ```
  Co-Authored-By: Gemini <noreply@google.com>
  ```
- Push your branch after each commit: `git push -u origin HEAD`.

---

## 4. The worklog — Mohamed audits this

After **every** step, append one entry to
[`docs/agent/WORKLOG.md`](docs/agent/WORKLOG.md). This is how Mohamed (and the
reviewer he brings in) rates your work without re-reading the whole diff. It is
append-only — never rewrite past entries. Format is defined at the top of that
file. An entry records: date, branch, what you did, the exact test command +
its result, the commit hash, and the PR number. No entry = the step didn't happen.

---

## 5. Merging — the hard gate

- The repo's `main` is **branch-protected**: PR required, two CI checks required
  (`Phase 0/1 tests` and `Phase 2 RTL`), no direct push, no force-push.
- **You may open PRs freely. You may NOT merge on your own initiative.** Merging
  is Mohamed's decision. Open the PR, get CI green, then wait. Only run
  `gh pr merge <N> --merge --delete-branch` after Mohamed explicitly types
  "merge" (or "merge everything", or names the PR). A generic "keep going" is
  **not** merge authorization.
- After a merge: `git checkout main && git pull`. If other PRs are open, they are
  now behind — rebase each on the new main and regenerate tracking (see PLAYBOOK).

---

## 6. Non-negotiables (the short avoid-list — full one in AVOID_LIST.md)

- ❌ Never edit a file you have not read this session.
- ❌ Never say "done/fixed/works" without a command output proving it.
- ❌ Never commit a design whose synth is not 0-latch or whose cocotb is not bit-exact.
- ❌ Never commit a formal proof without confirming it is **non-vacuous** (the
  `.smt2` actually contains `assert`s) and **mutation-tested** (corrupt the logic →
  proof FAILS; real logic → PASSES). Vacuous proofs are a known past bug here.
- ❌ Never inflate the tracker. `partial` ≠ `done`. Honesty over green checkmarks.
- ❌ Never `git checkout main` while a background merge/rebase job is using the tree.
- ❌ Never use `gh pr edit` (broken on this repo — GraphQL error). Use
  `gh api --method PATCH repos/Lord1Egypt/KemetCore/pulls/<N> -f title=.. -f body=..`.
- ❌ Never self-merge without Mohamed's explicit word.

---

## 7. When you are unsure

Stop and write the question into `docs/agent/WORKLOG.md` under a `NEEDS-MOHAMED`
heading, then work on something else that is unblocked. Do not guess on
irreversible or architectural decisions. Guessing on a wrong bit is worse than
waiting.

Full details: [`docs/agent/PLAYBOOK.md`](docs/agent/PLAYBOOK.md) ·
[`docs/agent/AVOID_LIST.md`](docs/agent/AVOID_LIST.md) ·
[`docs/agent/TASK_MENU.md`](docs/agent/TASK_MENU.md) ·
[`docs/agent/REVIEW_CHECKLIST.md`](docs/agent/REVIEW_CHECKLIST.md)
