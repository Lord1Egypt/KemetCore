#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the AnubisCore RTL.
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# Reports are written to reports/<core>.stat and committed as synthesis evidence.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports

for core in sha256_core sha3_224_core sha3_256_core sha3_384_core sha3_512_core sha512_core; do
    echo "=== synthesizing $core ==="
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done

# HMAC-SHA256 composes sha256_core, so its synthesis reads both sources.
echo "=== synthesizing hmac_sha256_core ==="
"$YOSYS" -ql "reports/hmac_sha256_core.log" -p "
    read_verilog -sv ../rtl/hmac_sha256_core.sv ../rtl/sha256_core.sv;
    synth -top hmac_sha256_core;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/hmac_sha256_core.stat stat
"
echo "  -> reports/hmac_sha256_core.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
