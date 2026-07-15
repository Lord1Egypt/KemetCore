# GOAL MODE — Autonomous Work → Verify → Review → Merge → Repeat

This is the autonomous operating mode. Mohamed enters it with the **`/goal`**
command. In GOAL MODE you drive KemetCore forward on your own — building, verifying,
self-reviewing, and **self-merging** — looping task after task until a STOP
condition. Mohamed and Claude review your trail between tasks and can interrupt at
any time. Autonomy is earned by discipline: the safety rails below are absolute.

---

## The autonomous loop (repeat until a STOP condition)

1. **Sync + sanity.** `git checkout main && git pull && pytest projects/ -q`.
   If pytest is red → STOP (halt, log it). Never build on red.
2. **Orient.** Read `docs/agent/RESUME.md` and `docs/agent/TASK_MENU.md`.
3. **STOP-check** (see STOP conditions). If any holds → write a final summary to
   `WORKLOG.md` + `RESUME.md` and halt.
4. **Pick ONE small task.** Branch: `git checkout -b feat/<core>-<thing>`.
5. **Read before writing** — golden model + neighbouring RTL + test harness.
6. **Build the smallest correct thing.** No stubs, no dead code, no scope creep.
7. **Verify ALL applicable gates — every one green, capture the output:**
   - cocotb bit-exact: `./projects/<core>/rtl/tb/run_sim.sh CORE=<x>`
   - Yosys 0-latch: `./projects/<core>/synth/run_synth.sh`
   - formal (if any): `./projects/<core>/formal/run_formal.sh` — AND prove it is
     **non-vacuous** (`grep -c assert build/*.smt2` > 0) AND **mutation-tested**
     (corrupt the logic → FAILED; restore → PROVED).
   - `pytest projects/ -q` if you touched golden/pymodel.
8. **If ANY gate fails →** fix the ROOT CAUSE and re-verify. Max **3** fix attempts
   on one task; if still failing, `git stash`/abandon the branch, write a
   `### NEEDS-MOHAMED` note in `WORKLOG.md`, and either move to a different task or
   STOP. **Never merge failing work. Never weaken a test to pass.**
9. **Self-review** against `docs/agent/REVIEW_CHECKLIST.md`. Every box must hold
   with real evidence. Update `tools/manifest.py` honestly (partial ≠ done) and run
   `python tools/gen_tracking.py`.
10. **Commit + push + log.** `git add -A && git commit && git push -u origin HEAD`;
    append a `WORKLOG.md` entry (test cmds + results + commit hash).
11. **Open PR** and **wait for CI** — poll `gh pr checks <N>` until BOTH required
    checks (`Phase 0/1 tests`, `Phase 2 RTL`) report **pass** (~25 min is normal).
12. **Merge gate — self-merge ONLY if ALL of these are true:**
    - every local gate in step 7 passed, AND
    - both required CI checks are **pass** (never merge on pending/red), AND
    - the self-review checklist is clean.
    Then: `gh pr merge <N> --merge --delete-branch` → `git checkout main && git pull`.
13. **Cut a rolling restore tag** right after the merge:
    `git tag -a safe-auto-<YYYY-MM-DD>-<n> -m "auto: after <task>" && git push origin <tag>`
    (increment `<n>` per merge that day). Every merged state is a restore point.
14. **Update `RESUME.md`** (state + next step) and loop back to step 1.

---

## HARD SAFETY RAILS (absolute — never violate, even to "make progress")

- ❌ **Never merge** if any local gate failed, CI is pending/red, or self-review is
  not clean. A red anything = do not merge, full stop.
- ❌ **Never** force-push, rewrite `main` history, delete tags, delete the backup
  folder, or change branch protection / repo settings.
- ❌ **Never** rewrite `AGENTS.md` or any `docs/agent/` contract file. The ONLY
  files you overwrite/append as state are `docs/agent/RESUME.md` and
  `docs/agent/WORKLOG.md`. (Also: always `git pull` main before branching so you
  have the latest kit — a stale branch is how duplicate AGENTS.md files happen.)
- ❌ **Never** batch unrelated changes — ONE task per PR.
- ❌ **Never** delete or `rm -rf` anything outside your own branch's build/ dirs.
- ❌ **Never** commit secrets, tokens, or keys.
- ❌ **Never** inflate the tracker. Honesty over green checkmarks.
- ❌ **Never** merge a formal proof that is vacuous or not mutation-tested.

## STOP conditions (halt, summarize in WORKLOG + RESUME, and wait for Mohamed)

- `TASK_MENU.md` has no remaining tractable task (project goal reached).
- A task needs a human/architectural decision (record `### NEEDS-MOHAMED`).
- The same task fails after 3 fix attempts.
- Any action would require something on the HARD RAILS list.
- CI is red for a reason you cannot fix at the root.
- A "bigger lever" task (full-core GDSII, RaCore SoC integration) is next — these
  need a plan approved by Mohamed before you start; propose the plan and STOP.

## What Mohamed / Claude do between your tasks
They read `WORKLOG.md` + the rolling `safe-auto-*` tags + your merged PRs, rate the
work, and either let you keep going or correct the road. You do not wait for them —
you keep looping — but they can interrupt at any time. Your job is to make that
review trivial: small PRs, honest logs, real evidence, one task at a time.

## Recovery (if something goes wrong)
Every merge leaves a `safe-auto-*` tag and there is a full folder backup
(`~/KemetCore_backup_<date>`). Worst case, Mohamed resets to a tag or restores the
backup — nothing is unrecoverable. That safety net is WHY autonomy is allowed; do
not treat it as license to skip a gate.
