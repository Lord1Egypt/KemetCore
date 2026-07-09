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
# a wrapper cannot reach the internal state/mode_reg regs); we compile with -DFORMAL
# and make the DUT the top. async2sync + dffunmap lower the async-reset DFFs that
# write_smt2 cannot emit raw. See formal/formal_ntt_ctrl.sv for the property notes.
prove_kind() {
    local top="$1" label="$2" tdepth="$3" srcs="$4"
    "$YOSYS" -ql "build/${top}.log" -p "read_verilog -sv -formal -DFORMAL ${srcs}; prep -top ${top}; async2sync; dffunmap; write_smt2 -wires build/${top}.smt2" >/dev/null 2>&1
    printf '%-24s ' "$label"
    "$SMTBMC" -s z3 -i -t "${tdepth}" "build/${top}.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅ (k-induction)" || { echo "FAILED ❌"; exit 1; }
}

prove formal_modmul "../rtl/neith_modmul.sv"
prove_kind neith_ntt formal_ntt_ctrl 6 "../rtl/neith_ntt.sv ../rtl/neith_butterfly.sv ../rtl/neith_modmul.sv"
echo "formal proofs PROVED ✅"
