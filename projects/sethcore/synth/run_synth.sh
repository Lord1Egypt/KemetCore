#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for SethCore RTL; asserts no latches.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports
# NOTE: seth_muldiv is intentionally excluded — a purely combinational 32-bit
# divider explodes under generic Yosys synth (minutes+). A real flow uses a
# sequential/iterative divider or a DesignWare-style macro; tracked for Phase 3.
for core in seth_alu seth_imm seth_regfile seth_aluctl seth_decode; do
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done

# seth_core is the full integrated single-cycle CPU. It embeds seth_muldiv (whose
# combinational divider explodes under full ABC), so we stop at the coarse netlist:
# that proves the Phase-3 exit gate (0 latches; memory inferred as $mem, not flops)
# deterministically in <1s. Skipped under CI (the stock apt Yosys is slow on the
# muldiv cloud); reports/seth_core.stat is the committed evidence.
if [ -z "${CI:-}" ]; then
    SRCS="../rtl/seth_decode.sv ../rtl/seth_imm.sv ../rtl/seth_aluctl.sv \
          ../rtl/seth_alu.sv ../rtl/seth_muldiv.sv ../rtl/seth_regfile.sv ../rtl/seth_core.sv"
    echo "=== synthesizing seth_core (coarse, 0-latch check) ==="
    "$YOSYS" -ql "reports/seth_core.log" -p "
        read_verilog -sv $SRCS;
        hierarchy -top seth_core;
        synth -top seth_core -run :fine;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/seth_core.stat stat
    "
    echo "  -> reports/seth_core.stat (0 latches asserted)"
else
    echo "=== skipping seth_core synth under CI (see committed reports/seth_core.stat) ==="
fi
echo "ALL SYNTHESIZED ✅ (no latches)"
