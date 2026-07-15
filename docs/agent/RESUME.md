# RESUME — Where We Are Right Now (read this first, keep it current)

> **This is the single "continue kemetcore" file.** When Mohamed says
> **"continue kemetcore"**, read this file top-to-bottom, then do exactly what
> **NEXT STEP** says. At the END of every session you MUST overwrite this file so
> the next session (or the next agent) resumes in 30 seconds. Keep it SHORT and
> TRUE — it is the current state, not a history (history lives in `WORKLOG.md`).

---

## Current state
- Successfully completed a "formal sweep" across the 4 remaining partial combinational properties in `TASK_MENU.md` (GebCore, PtahConv, ImentetCore, SobekCore, BastCore).
- All 5 formal properties are mutation-tested and passing in `yosys-smtbmc+z3`.
- PR #174 is open with all these changes and awaiting CI completion.
- Tracking matrix (`manifest.py` and `PROGRESS.md`) has been fully updated.
- The `/goal` for formal proofs is COMPLETE!

## NEXT STEP (do this when told "continue kemetcore")
1. Wait for CI to finish on PR #174. 
2. Once green, Mohamed can merge PR #174. 
3. After merging, cut a restore tag `safe-auto-<date>-N` if not already done.
4. Pull the latest `main` and pick a new breadth task from `TASK_MENU.md` (e.g. Phase-2 RTL breadth or Phase-4 P&R).

## Before you end EVERY session (mandatory)
- Overwrite the "Current state" + "NEXT STEP" above to reflect reality now
  (branch, last PR, what's done, the exact next action).
- Commit it: `git add docs/agent/RESUME.md && git commit -m "docs(agent): update RESUME state"`.
- Also save/refresh an Antigravity memory: **"KemetCore: to continue, open the repo
  and read docs/agent/RESUME.md, then follow AGENTS.md."** (see AGENTS.md §7).
