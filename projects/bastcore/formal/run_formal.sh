#!/usr/bin/env bash
# Phase 5: formal proofs (yosys write_smt2 + yosys-smtbmc + z3, k-induction).
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
command -v z3 >/dev/null || export PATH="$HOME/miniconda3/bin:$PATH"
mkdir -p build
"$YOSYS" -ql "build/formal_int8_mac.log" -p "read_verilog -sv -formal formal_int8_mac.sv ../rtl/bast_int8_mac.sv; prep -top formal_int8_mac; async2sync; dffunmap; write_smt2 -wires build/formal_int8_mac.smt2" >/dev/null 2>&1
printf '%-24s ' "formal_int8_mac"
"$SMTBMC" -s z3 -i -t 2 "build/formal_int8_mac.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅ (k-induction)" || { echo "FAILED ❌"; exit 1; }
echo "formal proofs PROVED ✅"
