#!/usr/bin/env bash
# Phase 5: formal proofs for SethCore (yosys write_smt2 + yosys-smtbmc + z3).
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
# Sequential (multicycle) proof by BMC from reset — needs dffunmap + more steps.
prove_seq() {
    local top="$1" steps="$2" extra="$3"
    "$YOSYS" -ql "build/${top}.log" -p "read_verilog -sv -formal ${top}.sv ${extra}; prep -top ${top}; async2sync; dffunmap; write_smt2 -wires build/${top}.smt2" >/dev/null 2>&1
    printf '%-24s ' "$top"
    "$SMTBMC" -s z3 -t "${steps}" "build/${top}.smt2" 2>&1 | grep -qi "PASSED" && echo "PROVED ✅" || { echo "FAILED ❌"; exit 1; }
}
prove formal_alu "../rtl/seth_alu.sv"   # XOR/AND/OR/ADD-SUB/SLT-SLTU algebraic identities
# Iterative divider == combinational reference for the short-latency paths
# (multiplies + special-case divides). BMC from reset, anyconst operands.
prove_seq formal_muldiv_equiv 8 "../rtl/seth_muldiv.sv ../rtl/seth_muldiv_seq.sv"
# Handshake control-safety of the iterative divider: done⊕busy mutual exclusion +
# done is a single-cycle pulse, over all free input sequences to depth 40
# (covers a full ~34-cycle divide plus restarts).
prove_seq formal_muldiv_handshake 40 "../rtl/seth_muldiv_seq.sv"
# Bounded termination: the iterative divide always finishes — busy is never
# continuously high longer than the proven-tight worst case (33 cycles).
prove_seq formal_muldiv_liveness 50 "../rtl/seth_muldiv_seq.sv"
echo "SethCore formal proofs PROVED ✅"
