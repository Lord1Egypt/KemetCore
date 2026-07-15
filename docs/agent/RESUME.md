# RESUME — Where We Are Right Now (read this first, keep it current)

> **This is the single "continue kemetcore" file.** When Mohamed says
> **"continue kemetcore"**, read this file top-to-bottom, then do exactly what
> **NEXT STEP** says. At the END of every session you MUST overwrite this file so
> the next session (or the next agent) resumes in 30 seconds. Keep it SHORT and
> TRUE — it is the current state, not a history (history lives in `WORKLOG.md`).

---

## Current state
- **Branch to work from:** `main` (tip after PR #179). ALWAYS `git pull` first.
- **Last verified:** AtumCore atum_vredu Phase 4 P&R + `/goal` mode merged (#179).
  Safe restore tags: `safe-auto-2026-07-15-4`.
- **Tests:** `pytest projects/ -q` → 146 passed (green).
- **Open PRs:** none. Clean slate.
- **⛔ Formal proofs are SATURATED** — do NOT re-run existing proofs or flip
  `partial`→`done`. See TASK_MENU "Formal breadth status".

## NEXT STEP (on "continue kemetcore" or `/goal`)
1. `git checkout main && git pull && pytest projects/ -q` (must be green).
2. Read the tail of `WORKLOG.md` to see the last few steps.
3. Pick ONE small **NEW** task from `TASK_MENU.md` — default: add one **Phase-2 RTL
   module** (a golden function with no RTL/testbench yet → build it bit-exact +
   0-latch) or harden one more **Phase-4 P&R block** to closed-timing GDSII.
   **NOT formal — it is saturated; do not re-run proofs or flip `partial`→`done`.**
4. Follow the loop in `PLAYBOOK.md` (in `/goal` mode, `GOAL_MODE.md`).

## Before you end EVERY session (mandatory)
- Overwrite the "Current state" + "NEXT STEP" above to reflect reality now
  (branch, last PR, what's done, the exact next action).
- Commit it: `git add docs/agent/RESUME.md && git commit -m "docs(agent): update RESUME state"`.
- Also save/refresh an Antigravity memory: **"KemetCore: to continue, open the repo
  and read docs/agent/RESUME.md, then follow AGENTS.md."** (see AGENTS.md §7).
