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
- **Date**: 2026-07-15
- **Branch**: `feat/sobekcore-cross-p4`
- **What**: Hardened `sobek_cross` on ASAP7 7nm (Phase 4 breadth). Added `sobek_cross_p4top` registered wrapper.
- **Verification**: `flow/harden.sh sobek_cross` → WNS 0.00 @ 111 MHz, 0 route-DRC.
- **Commit**: (HEAD)
- **PR**: #177

- **Date**: 2026-07-15
- **Branch**: `feat/hapicore-fp16-mul-p4`
- **What**: Hardened `hapi_fp16_mul` on ASAP7 7nm (Phase 4 breadth). Added `hapi_fp16_mul_p4top` registered wrapper.
- **Verification**: `flow/harden.sh hapi_fp16_mul` → WNS 0.00 @ 285 MHz, 0 route-DRC.
- **Commit**: (HEAD)
- **PR**: #178

- **Date**: 2026-07-15
- **Branch**: `feat/atumcore-vredu-p4`
- **What**: Hardened `atum_vredu` on ASAP7 7nm (Phase 4 breadth). Added `atum_vredu_p4top` registered wrapper.
- **Verification**: `flow/harden.sh atum_vredu` → WNS 0.00 @ 200 MHz, 0 route-DRC.
- **Commit**: (HEAD)
- **PR**: #179
2026-07-15 | `feat/ptahconv-bias-relu-p4` | Hardened ptah_bias_relu (Phase 4 P&R). Created wrapper ptah_bias_relu_p4top to bound 8x hapi_fp32_add and ReLUs. Configured OpenROAD for 166 MHz clock (6000 ps period). | `./flow/harden.sh ptah_bias_relu` | 0aa71a9 | #180
2026-07-15 | `feat/racore-kai-regs-p4` | Hardened ra_kai_regs (Phase 4 P&R). Configured OpenROAD for 666 MHz clock (1500 ps period). | `./flow/harden.sh ra_kai_regs` | b5f358d | #181
2026-07-15 | `feat/sethcore-muldiv-p4` | Hardened seth_muldiv (Phase 4 P&R). Created wrapper seth_muldiv_p4top to bound combinational logic. Configured OpenROAD for 100 MHz clock (10000 ps period). | `./flow/harden.sh seth_muldiv` | 088b9c80bfe3cb93fa3430feb82fd9ce71940564 | #182
2026-07-15 | `feat/ptahconv-avgpool-p4` | Hardened ptah_avgpool (Phase 4 P&R). Created wrapper ptah_avgpool_p4top to bound combinational logic. Configured OpenROAD for 100 MHz clock (10000 ps period). | `./flow/harden.sh ptah_avgpool` | TBD | #183
2026-07-15 | `feat/imentetcore-maskadd-p4` | Hardened imentet_mask_add (Phase 4 P&R). Created wrapper imentet_mask_add_p4top. Lowered utilization to 15% due to 768 pins causing routing congestion. Configured OpenROAD for 50 MHz clock (20000 ps period). | `./flow/harden.sh imentet_mask_add` | TBD | #184
2026-07-15 | `feat/sobekcore-scale-p4` | Hardened sobek_scale (Phase 4 P&R). Created wrapper sobek_scale_p4top. P&R closed timing cleanly at 111 MHz (9000 ps period). | `./flow/harden.sh sobek_scale` | TBD | #185
2026-07-15 | `feat/atumcore-vsadd-p4` | Hardened atum_vsadd (Phase 4 P&R). Created wrapper atum_vsadd_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). Lowered utilization to 15% to accommodate >1k pins. | `./flow/harden.sh atum_vsadd` | TBD | #186
2026-07-15 | `feat/atumcore-vcompress-p4` | Hardened atum_vcompress (Phase 4 P&R). Created wrapper atum_vcompress_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh atum_vcompress` | TBD | #187
2026-07-15 | `feat/neithcore-polyaddsub-p4` | Hardened neith_polyaddsub (Phase 4 P&R). Created wrapper neith_polyaddsub_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh neith_polyaddsub` | TBD | #188
2026-07-15 | `feat/hapicore-fp32-to-int-p4` | Hardened hapi_fp32_to_int (Phase 4 P&R). Created wrapper hapi_fp32_to_int_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh hapi_fp32_to_int` | TBD | #189
2026-07-15 | `feat/atumcore-viota-p4` | Hardened atum_viota (Phase 4 P&R). Created wrapper atum_viota_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh atum_viota` | TBD | #190
2026-07-15 | `feat/atumcore-vmask-p4` | Hardened atum_vmask (Phase 4 P&R). Created wrapper atum_vmask_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh atum_vmask` | TBD | #191
2026-07-15 | `feat/neithcore-butterfly-p4` | Hardened neith_butterfly (Phase 4 P&R). Created wrapper neith_butterfly_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh neith_butterfly` | TBD | #192
2026-07-15 | `feat/sobekcore-lerp-p4` | Hardened sobek_lerp (Phase 4 P&R). Created wrapper sobek_lerp_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh sobek_lerp` | TBD | #193
2026-07-15 | `feat/sobekcore-ray-point-p4` | Hardened sobek_ray_point (Phase 4 P&R). Created wrapper sobek_ray_point_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh sobek_ray_point` | TBD | #194
2026-07-15 | `feat/sobekcore-faceforward-p4` | Hardened sobek_faceforward (Phase 4 P&R). Created wrapper sobek_faceforward_p4top. P&R closed timing cleanly at 100 MHz (10000 ps period). | `./flow/harden.sh sobek_faceforward` | TBD | #195
2026-07-15 | `feat/sobekcore-length` (Abandoned) | Attempted to harden sobek_length (Phase 4 P&R) but it uses a deep 54-bit integer square root unrolled 27 times + 3 muls + 2 adds. Failed to close timing at 100MHz (WNS ~ -9ns). Abandoned. | `./flow/harden.sh sobek_length` | FAIL | N/A

### 2026-07-16 - feat/hapi_bf16_mul_p4
- **Task:** Harden `hapi_bf16_mul` (Phase 4 P&R).
- **Action:** Created `hapi_bf16_mul_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_bf16_mul` finished with WNS=0.00, 119.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending


### 2026-07-16 - feat/hapi_bf16_add_p4
- **Task:** Harden `hapi_bf16_add` (Phase 4 P&R).
- **Action:** Created `hapi_bf16_add_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_bf16_add` finished with WNS=0.00, 151.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending


### 2026-07-16 - feat/hapi_fp16_add_p4
- **Task:** Harden `hapi_fp16_add` (Phase 4 P&R).
- **Action:** Created `hapi_fp16_add_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_fp16_add` finished with WNS=0.00, 179.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending


### 2026-07-16 - feat/hapi_fp32_to_bf16_p4
- **Task:** Harden `hapi_fp32_to_bf16` (Phase 4 P&R).
- **Action:** Created `hapi_fp32_to_bf16_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_fp32_to_bf16` finished with WNS=0.00, 27.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending


### 2026-07-16 - feat/hapi_fp32_to_fp16_p4
- **Task:** Harden `hapi_fp32_to_fp16` (Phase 4 P&R).
- **Action:** Created `hapi_fp32_to_fp16_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_fp32_to_fp16` finished with WNS=0.00, 81.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending


### 2026-07-16 - feat/hapi_bf16_to_fp32_p4
- **Task:** Harden `hapi_bf16_to_fp32` (Phase 4 P&R).
- **Action:** Created `hapi_bf16_to_fp32_p4top` registered wrapper and ASAP7 configs. Ran OpenROAD flow.
- **Verification:** `./flow/harden.sh hapi_bf16_to_fp32` finished with WNS=0.00, 17.0 um^2 area, 0 routing DRC violations.
- **Commit:** pending
- **PR:** pending

