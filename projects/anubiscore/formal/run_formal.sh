#!/usr/bin/env bash
# Phase 5: formal proofs (yosys write_smt2 + yosys-smtbmc + z3, k-induction).
# AnubisCore: SHA-256 FSM control-safety (round counter bounded + no illegal state).
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
command -v z3 >/dev/null || export PATH="$HOME/miniconda3/bin:$PATH"
mkdir -p build

"$YOSYS" -ql "build/formal_sha256_ctrl.log" -p "read_verilog -sv -formal formal_sha256_ctrl.sv ../rtl/sha256_core.sv; prep -top formal_sha256_ctrl; async2sync; dffunmap; write_smt2 -wires build/formal_sha256_ctrl.smt2" >/dev/null 2>&1
printf '%-24s ' "formal_sha256_ctrl"
"$SMTBMC" -s z3 -i -t 4 "build/formal_sha256_ctrl.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅ (k-induction)" || { echo "FAILED ❌"; exit 1; }

echo "formal proofs PROVED ✅"
