#!/usr/bin/env bash
# Phase 5: formal proofs (yosys write_smt2 + yosys-smtbmc + z3).
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
command -v z3 >/dev/null || export PATH="$HOME/miniconda3/bin:$PATH"
mkdir -p build
prove() {
    local top="$1" extra="$2"
    "$YOSYS" -ql "build/${top}.log" -p "read_verilog -sv -formal ${top}.sv ${extra}; prep -top ${top}; async2sync; write_smt2 -wires build/${top}.smt2" >/dev/null 2>&1
    printf '%-24s ' "$top"
    "$SMTBMC" -s z3 -t 1 "build/${top}.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅" || { echo "FAILED ❌"; exit 1; }
}
# Sequential FSM proof by temporal k-induction. Assertions are embedded in the DUT
# under `ifdef FORMAL (yosys 0.65 supports neither hierarchical refs nor `bind`, so
# a wrapper cannot reach the internal state/done regs); we compile with -DFORMAL and
# make the DUT the top. ptah_conv2d has a SYNC reset (no async init), and both
# invariants are 1-inductive, so we use k-induction (-i) rather than plain BMC —
# see formal/formal_conv2d_ctrl.sv for the property + method notes.
prove_kind() {
    local top="$1" label="$2" tdepth="$3" srcs="$4"
    "$YOSYS" -ql "build/${top}.log" -p "read_verilog -sv -formal -DFORMAL ${srcs}; prep -top ${top}; async2sync; dffunmap; write_smt2 -wires build/${top}.smt2" >/dev/null 2>&1
    printf '%-24s ' "$label"
    "$SMTBMC" -s z3 -i -t "${tdepth}" "build/${top}.smt2" 2>&1 | grep -qi "Status: PASSED" && echo "PROVED ✅ (k-induction)" || { echo "FAILED ❌"; exit 1; }
}

prove formal_bias_relu "../rtl/ptah_bias_relu.sv ../../hapicore/rtl/hapi_fp32_add.sv"
prove_kind ptah_conv2d formal_conv2d_ctrl 8 "../rtl/ptah_conv2d.sv ../rtl/ptah_mac.sv ../../hapicore/rtl/hapi_fp32_add.sv ../../hapicore/rtl/hapi_fp32_mul.sv"
echo "formal proofs PROVED ✅"
