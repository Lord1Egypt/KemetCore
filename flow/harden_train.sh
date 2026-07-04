#!/usr/bin/env bash
# Harden a batch of KemetCore designs to GDSII one after another and summarise
# each (area / timing / DRC). Usage: flow/harden_train.sh sha256_core seth_regfile ...
set -uo pipefail
cd "$(dirname "$0")/.."
SUMMARY="flow/HARDEN_RESULTS.md"
echo "# KemetCore — GDSII harden results" > "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| design | GDS | area (µm²) | WNS (ps) | antenna DRC | RAM (MB) |" >> "$SUMMARY"
echo "|--------|:---:|-----------:|---------:|:-----------:|---------:|" >> "$SUMMARY"

for d in "$@"; do
  echo "[$(date +%H:%M:%S)] ▶ hardening $d"
  ORFS_MAKE_ARGS='NUM_CORES=4' ./flow/harden.sh "$d" >/dev/null 2>&1 || true
  R="flow/results/asap7/$d/base"; L="flow/logs/asap7/$d/base"; RP="flow/reports/asap7/$d/base"
  if [ -f "$R/6_final.gds" ]; then
    gds="✅ $(du -h "$R/6_final.gds" | cut -f1)"
    area=$(grep -iE "Design area" "$L/6_report.log" 2>/dev/null | tail -1 | grep -oE "[0-9]+ um" | grep -oE "[0-9]+")
    wns=$(grep -iE "^wns max|worst slack max" "$RP/6_finish.rpt" 2>/dev/null | grep -oE "\-?[0-9.]+" | head -1)
    drc=$(grep -c "Found 0 .* violations" "$L/5_2_route.log" 2>/dev/null || echo "?")
    ram=$(grep -iE "Peak memory" "$L/5_2_route.log" 2>/dev/null | grep -oE "[0-9]+" | tail -1)
    echo "| \`$d\` | $gds | ${area:-?} | ${wns:-?} | ${drc:-?}× clean | ${ram:-?} |" >> "$SUMMARY"
    echo "[$(date +%H:%M:%S)]   ✅ $d -> GDS (${area:-?} um^2, WNS ${wns:-?} ps)"
  else
    laststage=$(ls -t "$R"/*.odb 2>/dev/null | head -1 | xargs -n1 basename 2>/dev/null)
    echo "| \`$d\` | ❌ | — | — | — | — | (stopped at ${laststage:-?}) |" >> "$SUMMARY"
    echo "[$(date +%H:%M:%S)]   ❌ $d -> no GDS (last: ${laststage:-?})"
  fi
done
echo "[$(date +%H:%M:%S)] === HARDEN TRAIN DONE — see $SUMMARY ==="
cat "$SUMMARY"
