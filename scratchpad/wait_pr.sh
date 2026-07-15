#!/usr/bin/env bash
# Poll a PR's checks until the two required gates + the formal job resolve.
# Usage: wait_pr.sh <PR#>
set -uo pipefail
PR="$1"
cd "$(dirname "$0")/.."
while true; do
  out="$(gh pr checks "$PR" 2>/dev/null)"
  req_ok=1; any_fail=0
  while IFS=$'\t' read -r name state rest; do
    case "$name" in
      "Phase 0/1 tests"*|"Phase 2 RTL"*|"Phase 5 formal"*)
        [ "$state" = "pass" ] || req_ok=0
        [ "$state" = "fail" ] && any_fail=1 ;;
    esac
  done <<< "$out"
  if [ "$any_fail" = "1" ]; then echo "FAILED"; echo "$out"; exit 1; fi
  if [ "$req_ok" = "1" ]; then echo "ALL GREEN"; echo "$out"; exit 0; fi
  sleep 60
done
