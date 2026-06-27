#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the HapiCore FPU datapath (bf16 + fp32).
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# Reports are written to reports/<core>.stat and committed as synthesis evidence.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports

for core in hapi_bf16_mul hapi_bf16_add hapi_fp32_mul hapi_fp32_add hapi_fp16_mul; do
    echo "=== synthesizing $core ==="
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done
echo "ALL SYNTHESIZED ✅ (no latches)"
