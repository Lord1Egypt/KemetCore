# RESUME — Where We Are Right Now (read this first, keep it current)

> **This is the single "continue kemetcore" file.** When Mohamed says
> **"continue kemetcore"**, read this file top-to-bottom, then do exactly what
> **NEXT STEP** says. At the END of every session you MUST overwrite this file so
> the next session (or the next agent) resumes in 30 seconds. Keep it SHORT and
> TRUE — it is the current state, not a history (history lives in `WORKLOG.md`).

---

## Current state
- **Branch to work from:** `main` (branch off it for each task).
- **main tip / last verified:** `4022947` (merge PR #172). Safe restore tag:
  `safe-baseline-2026-07-15`.
- **Tests:** `pytest projects/ -q` → 146 passed (green).
- **Tracker:** 34% (23/66). All 11 cores P0/P1 ✅; P2/P3/P4/P5 partial 🔧.
- **Open PRs:** #173 (docs — the agent instruction set; may already be merged).
- **Anything half-finished?** No RTL/formal work in flight. Clean slate.

## NEXT STEP (do this when told "continue kemetcore")
1. `git checkout main && git pull && pytest projects/ -q` (must be green).
2. Read the tail of `WORKLOG.md` to see the last few steps.
3. Pick ONE small task from `TASK_MENU.md` (default: add one Phase-2 RTL module
   bit-exact vs golden, or harden one more Phase-4 block, or deepen one tractable
   formal proof).
4. Follow the loop in `PLAYBOOK.md`. Stop at the PR — do NOT merge.

## Before you end EVERY session (mandatory)
- Overwrite the "Current state" + "NEXT STEP" above to reflect reality now
  (branch, last PR, what's done, the exact next action).
- Commit it: `git add docs/agent/RESUME.md && git commit -m "docs(agent): update RESUME state"`.
- Also save/refresh an Antigravity memory: **"KemetCore: to continue, open the repo
  and read docs/agent/RESUME.md, then follow AGENTS.md."** (see AGENTS.md §7).
