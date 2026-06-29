#!/usr/bin/env bash
# Phase 3: Yosys synthesis for the RaCore KAI register block; asserts no latches.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports
echo "=== synthesizing ra_kai_regs ==="
"$YOSYS" -ql "reports/ra_kai_regs.log" -p "
    read_verilog -sv ../rtl/ra_kai_regs.sv;
    synth -top ra_kai_regs;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_kai_regs.stat stat
"
echo "  -> reports/ra_kai_regs.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
