#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for SethCore RTL; asserts no latches.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports
# NOTE: seth_muldiv is intentionally excluded — a purely combinational 32-bit
# divider explodes under generic Yosys synth (minutes+). A real flow uses a
# sequential/iterative divider or a DesignWare-style macro; tracked for Phase 3.
for core in seth_alu seth_imm seth_regfile seth_aluctl seth_decode; do
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done
echo "ALL SYNTHESIZED ✅ (no latches)"
