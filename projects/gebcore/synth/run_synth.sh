#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the GebCore 2:4 sparse-MAC cell.
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# geb_spmac instantiates the HapiCore fp32 primitives, so they are read in too.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
HAPI=../../hapicore/rtl
mkdir -p reports

echo "=== synthesizing geb_spmac ==="
"$YOSYS" -ql "reports/geb_spmac.log" -p "
    read_verilog -sv ${HAPI}/hapi_fp32_mul.sv ${HAPI}/hapi_fp32_add.sv ../rtl/geb_spmac.sv;
    synth -top geb_spmac;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/geb_spmac.stat stat
"
echo "  -> reports/geb_spmac.stat (0 latches asserted)"

echo "=== synthesizing geb_prune ==="
"$YOSYS" -ql "reports/geb_prune.log" -p "
    read_verilog -sv ../rtl/geb_prune.sv;
    synth -top geb_prune;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/geb_prune.stat stat
"
echo "  -> reports/geb_prune.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
