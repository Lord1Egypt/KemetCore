#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the PtahConv fp32 MAC cell; asserts no latches.
# ptah_mac instantiates the HapiCore fp32 primitives, so they are read in too.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
HAPI=../../hapicore/rtl
mkdir -p reports

echo "=== synthesizing ptah_mac ==="
"$YOSYS" -ql "reports/ptah_mac.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/ptah_mac.sv;
    synth -top ptah_mac;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ptah_mac.stat stat
"
echo "  -> reports/ptah_mac.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
