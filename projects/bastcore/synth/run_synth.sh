#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the BastCore MAC cell.
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# bast_mac instantiates the HapiCore primitives, so they are read in too.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
HAPI=../../hapicore/rtl
mkdir -p reports

echo "=== synthesizing bast_mac ==="
"$YOSYS" -ql "reports/bast_mac.log" -p "
    read_verilog -sv ${HAPI}/hapi_bf16_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/bast_mac.sv;
    synth -top bast_mac;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/bast_mac.stat stat
"
echo "  -> reports/bast_mac.stat (0 latches asserted)"

echo "=== synthesizing bast_mac_grid (default 4x4 systolic array) ==="
"$YOSYS" -ql "reports/bast_mac_grid.log" -p "
    read_verilog -sv ${HAPI}/hapi_bf16_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/bast_mac.sv ../rtl/bast_mac_grid.sv;
    synth -top bast_mac_grid;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/bast_mac_grid.stat stat
"
echo "  -> reports/bast_mac_grid.stat (0 latches asserted)"

echo "=== synthesizing bast_int8_mac ==="
"$YOSYS" -ql "reports/bast_int8_mac.log" -p "
    read_verilog -sv ../rtl/bast_int8_mac.sv;
    synth -top bast_int8_mac;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/bast_int8_mac.stat stat
"
echo "  -> reports/bast_int8_mac.stat (0 latches asserted)"

echo "=== synthesizing bast_int8_grid (default 4x4 INT8 systolic array) ==="
"$YOSYS" -ql "reports/bast_int8_grid.log" -p "
    read_verilog -sv ../rtl/bast_int8_mac.sv ../rtl/bast_int8_grid.sv;
    synth -top bast_int8_grid;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/bast_int8_grid.stat stat
"
echo "  -> reports/bast_int8_grid.stat (0 latches asserted)"
echo "=== synthesizing bast_fp16_mac ==="
"$YOSYS" -ql "reports/bast_fp16_mac.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp16_mul.sv ${HAPI}/hapi_fp16_to_fp32.sv ${HAPI}/hapi_fp32_add.sv ../rtl/bast_fp16_mac.sv;
    synth -top bast_fp16_mac;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/bast_fp16_mac.stat stat
"
echo "  -> reports/bast_fp16_mac.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
