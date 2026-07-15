#!/usr/bin/env bash
# Autonomous merge train for session-D PRs: merge #171 (ptahconv) once its CI is
# green, then de-stack + rebase #172 (atumcore) onto the new main, push, wait
# green, merge. Robust to the generated-file (PROGRESS.md/CHECKPOINTS.md) churn.
set -uo pipefail
cd /home/lordegypt/KemetCore
export PATH="$HOME/miniconda3/bin:$PATH"
LOG=scratchpad/merge_train_d.log
echo "=== merge_train_d start $(date) ===" > $LOG

checks_green() { # $1=PR -> 0 if BOTH required checks pass
  local out; out=$(gh pr checks "$1" 2>/dev/null)
  echo "$out" | grep -q "Phase 0/1 tests.*pass" && \
  echo "$out" | grep -q "Phase 2 RTL.*pass"
}
wait_green() { # $1=PR
  for i in $(seq 1 120); do
    if gh pr checks "$1" 2>/dev/null | grep -Eq "fail|error"; then echo "PR $1 has FAILING checks" >>$LOG; return 1; fi
    checks_green "$1" && { echo "PR $1 checks green (try $i)" >>$LOG; return 0; }
    sleep 45
  done
  echo "PR $1 timed out waiting for checks" >>$LOG; return 1
}

# ---- 1. #171 ----
echo "waiting on #171 CI..." >>$LOG
wait_green 171 || { echo "ABORT at #171" >>$LOG; exit 1; }
gh pr merge 171 --merge --delete-branch >>$LOG 2>&1
sleep 4
[ "$(gh pr view 171 --json state -q .state)" = "MERGED" ] || { echo "ABORT: #171 not merged" >>$LOG; exit 1; }
echo "#171 MERGED" >>$LOG
git checkout -q main && git pull -q origin main

# ---- 2. de-stack + rebase #172 ----
git fetch -q origin
git checkout -q feat/phase5-atum-vcore-ctrl
git rebase origin/main >>$LOG 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  # resolve generated-file conflicts by regenerating; keep going
  git checkout --theirs PROGRESS.md projects/*/CHECKPOINTS.md >>$LOG 2>&1
  git add -A >>$LOG 2>&1
  GIT_EDITOR=true git rebase --continue >>$LOG 2>&1 || { git rebase --abort; echo "ABORT: #172 rebase conflict needs human" >>$LOG; exit 1; }
fi
python3 tools/gen_tracking.py >/dev/null 2>&1
git add PROGRESS.md projects/atumcore/CHECKPOINTS.md tools/manifest.py >>$LOG 2>&1
git diff --cached --quiet || GIT_EDITOR=true git commit --amend --no-edit >>$LOG 2>&1
# sanity: atumcore-only diff (ptahconv must be gone)
if git diff --name-only origin/main..HEAD | grep -q ptahconv; then echo "ABORT: #172 still carries ptahconv after rebase" >>$LOG; exit 1; fi
git push --force-with-lease >>$LOG 2>&1
echo "#172 rebased+pushed (atumcore-only)" >>$LOG

# ---- 3. #172 ----
sleep 20
wait_green 172 || { echo "ABORT at #172 (CI)" >>$LOG; exit 1; }
gh pr merge 172 --merge --delete-branch >>$LOG 2>&1
sleep 4
[ "$(gh pr view 172 --json state -q .state)" = "MERGED" ] || { echo "ABORT: #172 not merged" >>$LOG; exit 1; }
echo "#172 MERGED" >>$LOG
git checkout -q main && git pull -q origin main
echo "=== TRAIN COMPLETE $(date) — all 3 PRs merged ===" >>$LOG
