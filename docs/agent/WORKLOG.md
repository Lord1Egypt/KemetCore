# WORKLOG — Append-Only Record of Every Step

**Rules:**
- Append a new entry after **every** step. Newest at the BOTTOM. Never rewrite or
  delete past entries — this is the audit trail Mohamed rates you against.
- If you are blocked, add an entry under a `### NEEDS-MOHAMED` heading describing
  the decision you need, then work on something unblocked.
- One entry = one verified step. No entry = the step didn't happen.

**Entry format (copy this):**

```
### <YYYY-MM-DD> — <branch> — <one-line what>
- **Did:** <what you built/changed, which files>
- **Verified:** <exact command> → <result, e.g. "cocotb PASS bit-exact / 0 latches / Status: PASSED">
- **Tracking:** <manifest checkpoint id added, or "no status change">
- **Commit:** <hash> · **PR:** #<N> (<CI state>)
- **Self-rating:** <what shipped · strongest evidence · weakest/least-certain part>
```

---

### 2026-07-15 — main — Agent instruction set handed off
- **Did:** Created the agent operating contract: `AGENTS.md` + `GEMINI.md` at repo
  root, and `docs/agent/` (PLAYBOOK, AVOID_LIST, TASK_MENU, REVIEW_CHECKLIST, this
  WORKLOG). No source/RTL changed.
- **Verified:** N/A (docs only). Repo state confirmed: `main` clean, no open PRs,
  `pytest projects/ -q` green at handoff.
- **Tracking:** no status change.
- **Commit:** (this handoff commit) · **PR:** docs handoff
- **Self-rating:** Onboarding docs for the Gemini/Antigravity agent to continue
  KemetCore. Strongest evidence: paths/commands verified against the live repo and
  toolchain this session. Weakest part: the exact Antigravity config-file auto-load
  name may vary by version — `AGENTS.md` and `GEMINI.md` cover the common cases; if
  Antigravity looks for a different filename, symlink or copy `AGENTS.md` to it.

### 2026-07-15 — SAFE CHECKPOINT tagged before autonomous work
- **Did:** Created annotated git tag `safe-baseline-2026-07-15` on the last
  fully-verified commit `4022947` (merge PR #172). Pushed to origin.
- **Why:** Restore point in case autonomous work breaks something.
- **State at tag:** all 11 cores Phase 0/1 green (`pytest projects/ -q` = 146
  passed), tracker 34%, no open code PRs (only docs PR #173).
- **RESTORE INSTRUCTIONS (for Mohamed or Gemini):**
  - See the exact good state: `git show safe-baseline-2026-07-15`
  - Reset a local branch back to it: `git reset --hard safe-baseline-2026-07-15`
  - `main` is branch-protected (no force-push). To roll `main` back, open a PR
    that resets content to the tag, or `git revert` the bad merge commits.
  - The tag is immutable and on the remote — it cannot be lost by local mistakes.

<!-- Gemini: append your entries below this line -->

### 2026-07-15 — feat/gebcore-formal-prune — GebCore geb_prune full 2:4 formal proof (agy)
- **Did (agy):** Extended the geb_prune formal proof from "exactly 2 kept" to full
  functional correctness — embedded asserts in `projects/gebcore/rtl/geb_prune.sv`
  under `` `ifdef FORMAL `` (exactly-2-kept + kept value/index match + every kept
  lane's magnitude beats every dropped lane). Added `-DFORMAL` to run_formal.sh.
- **Verified (agy):** run_formal.sh → PROVED; run_sim.sh CORE=prune → PASS; synth → 0 latches.
- **Reviewed (Claude, re-ran all gates):** PROVED with **76 asserts in the .smt2
  (non-vacuous)**; **two independent mutations both → FAILED** (live proof);
  cocotb `test_prune PASS`; synth `geb_prune 0 latches`. RTL inspected — `beats()`
  is a correct total order, so the value/index + dominance properties are genuine.
  **Verdict: PASS.** Reconciled onto canonical main (dropped agy's duplicate
  AGENTS.md; kept the proof + G.7=done). Honest: only the G.7 checkpoint flips to
  done; P5 phase % unchanged.
- **Tracking:** G.7 partial→done (gebcore 5/7 checkpoints).
- **PR:** #174 (reconciled).
