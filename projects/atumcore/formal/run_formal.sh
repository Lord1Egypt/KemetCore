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
# Sequential control-safety proof by temporal k-induction. Assertions are embedded
# in the DUT under `ifdef FORMAL (yosys 0.65 supports neither hierarchical refs nor
# `bind, so a wrapper cannot reach the internal vl/halted regs); compile with
# -DFORMAL. The heavy vector datapath (atum_vexec/atum_vregfile and their divider/
# sqrt/fp sub-tree) is BLACKBOXED — vl/halted/pc do not depend on their outputs —
# so z3 stays fast. See formal/formal_vcore_ctrl.sv for the property notes.
prove_vcore() {
    "$YOSYS" -ql "build/atum_vcore.log" -p "read_verilog -sv -formal -DFORMAL ../rtl/atum_vcore.sv ../rtl/atum_vsetvl.sv ../rtl/atum_vexec.sv ../rtl/atum_vregfile.sv; blackbox atum_vexec atum_vregfile; hierarchy -top atum_vcore; prep -top atum_vcore; async2sync; dffunmap; write_smt2 -wires build/atum_vcore.smt2" >/dev/null 2>&1
    printf '%-24s ' "formal_vcore_ctrl"
    "$SMTBMC" -s z3 -i -t 8 "build/atum_vcore.smt2" 2>&1 | grep -qi "Status: PASSED" && echo "PROVED ✅ (k-induction)" || { echo "FAILED ❌"; exit 1; }
}

prove formal_valu "../rtl/atum_valu.sv"
prove_vcore
echo "formal proofs PROVED ✅"
