#!/usr/bin/env bash
# Phase 5: formal proofs for HapiCore (yosys write_smt2 + yosys-smtbmc + z3).
# All properties are combinational, so one BMC step proves them for ALL inputs.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
command -v z3 >/dev/null || export PATH="$HOME/miniconda3/bin:$PATH"
mkdir -p build
prove() { # <top> <extra-src>
    local top="$1" extra="$2"
    "$YOSYS" -ql "build/${top}.log" -p "read_verilog -sv -formal ${top}.sv ${extra}; prep -top ${top}; write_smt2 -wires build/${top}.smt2" >/dev/null 2>&1
    printf '%-24s ' "$top"
    "$SMTBMC" -s z3 -t 1 "build/${top}.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅" || { echo "FAILED ❌"; exit 1; }
}
prove formal_fp32_mul "../rtl/hapi_fp32_mul.sv"   # commutativity + sign
prove formal_fp32_add "../rtl/hapi_fp32_add.sv"   # commutativity
echo "HapiCore formal proofs PROVED ✅"
