#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the NeithCore NTT primitives.
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# Reports are written to reports/<core>.stat and committed as synthesis evidence.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports

# neith_modmul: standalone. neith_butterfly: pulls in neith_modmul too.
echo "=== synthesizing neith_modmul ==="
"$YOSYS" -ql "reports/neith_modmul.log" -p "
    read_verilog -sv ../rtl/neith_modmul.sv;
    synth -top neith_modmul;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/neith_modmul.stat stat
"
echo "  -> reports/neith_modmul.stat (0 latches asserted)"

echo "=== synthesizing neith_butterfly ==="
"$YOSYS" -ql "reports/neith_butterfly.log" -p "
    read_verilog -sv ../rtl/neith_modmul.sv ../rtl/neith_butterfly.sv;
    synth -top neith_butterfly;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/neith_butterfly.stat stat
"
echo "  -> reports/neith_butterfly.stat (0 latches asserted)"

echo "=== synthesizing neith_ntt (256-point engine) ==="
"$YOSYS" -ql "reports/neith_ntt.log" -p "
    read_verilog -sv ../rtl/neith_modmul.sv ../rtl/neith_butterfly.sv ../rtl/neith_ntt.sv;
    synth -top neith_ntt;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/neith_ntt.stat stat
"
echo "  -> reports/neith_ntt.stat (0 latches asserted)"

echo "=== synthesizing neith_pointwise (NTT-domain pointwise multiply) ==="
"$YOSYS" -ql "reports/neith_pointwise.log" -p "
    read_verilog -sv ../rtl/neith_modmul.sv ../rtl/neith_pointwise.sv;
    synth -top neith_pointwise;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/neith_pointwise.stat stat
"
echo "  -> reports/neith_pointwise.stat (0 latches asserted)"

echo "=== synthesizing neith_polyaddsub (polynomial mod add/sub) ==="
"$YOSYS" -ql "reports/neith_polyaddsub.log" -p "
    read_verilog -sv ../rtl/neith_polyaddsub.sv;
    synth -top neith_polyaddsub;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/neith_polyaddsub.stat stat
"
echo "  -> reports/neith_polyaddsub.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
