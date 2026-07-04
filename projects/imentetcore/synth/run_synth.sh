#!/usr/bin/env bash
# Phase 3: Yosys synthesis for ImentetCore RTL; asserts no latches.
# imentet_qk_score instantiates the HapiCore fp32 primitives, so they are read in.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
HAPI=../../hapicore/rtl
mkdir -p reports

echo "=== synthesizing imentet_qk_score ==="
"$YOSYS" -ql "reports/imentet_qk_score.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/imentet_qk_score.sv;
    synth -top imentet_qk_score;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/imentet_qk_score.stat stat
"
echo "  -> reports/imentet_qk_score.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
