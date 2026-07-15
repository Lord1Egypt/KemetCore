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

### 2026-07-15 — GebCore: geb_prune formal 2:4 invariant
- **Branch:** feat/gebcore-formal-prune
- **Did:** Added embedded asserts to `projects/gebcore/rtl/geb_prune.sv` under `ifdef FORMAL` to prove the 2:4 structured-sparsity invariant (exactly 2 kept, and output values match inputs). Modified `run_formal.sh` to compile it with `-DFORMAL` natively.
- **Verification:**
  - Mutation-tested by temporarily changing the kept limit to 3 -> `FAILED ❌`.
  - `projects/gebcore/formal/run_formal.sh` -> `formal_prune PROVED ✅`
  - `projects/gebcore/rtl/tb/run_sim.sh CORE=prune` -> `test_prune passed (1/1)`
  - `projects/gebcore/synth/run_synth.sh` -> `0 latches asserted`
- **Commit:** 509c6da
- **PR:** 174

### 2026-07-15 — Formal Sweeps: PtahConv, ImentetCore, SobekCore, BastCore
- **Branch:** feat/gebcore-formal-prune
- **Did:** Mutation-tested and formally verified 4 existing partial combinational properties:
  - `ptah_bias_relu` non-negativity (PC.5)
  - `imentet_mask_add` masking semantics (I.6)
  - `sobek_scale` multiply-commutativity (SB.5)
  - `bast_int8_mac` multiply-commutativity (B2.10)
- **Verification:** All 4 proofs were mutated to intentionally fail (`FAILED ❌`), then restored and proved non-vacuous (`PROVED ✅`). Synthesized and simulated to ensure 0-latch and bit-exactness. All gates passed.
- **Commit:** (pending)
- **PR:** 174 (Updated PR scope to encompass these sweeps)
<!-- Gemini: append your entries below this line -->
