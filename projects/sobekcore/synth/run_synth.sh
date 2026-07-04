#!/usr/bin/env bash
# Phase 3: Yosys synthesis for SobekCore RTL; asserts no latches.
# sobek_dot3 instantiates the HapiCore fp32 primitives, so they are read in too.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
HAPI=../../hapicore/rtl
mkdir -p reports

echo "=== synthesizing sobek_dot3 ==="
"$YOSYS" -ql "reports/sobek_dot3.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/sobek_dot3.sv;
    synth -top sobek_dot3;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/sobek_dot3.stat stat
"
echo "  -> reports/sobek_dot3.stat (0 latches asserted)"

echo "=== synthesizing sobek_cross ==="
"$YOSYS" -ql "reports/sobek_cross.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/sobek_cross.sv;
    synth -top sobek_cross;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/sobek_cross.stat stat
"
echo "  -> reports/sobek_cross.stat (0 latches asserted)"

echo "=== synthesizing sobek_scale ==="
"$YOSYS" -ql "reports/sobek_scale.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ../rtl/sobek_scale.sv;
    synth -top sobek_scale;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/sobek_scale.stat stat
"
echo "  -> reports/sobek_scale.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
