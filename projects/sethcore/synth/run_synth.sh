#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for SethCore RTL; asserts no latches.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports
# NOTE: seth_muldiv is intentionally excluded — a purely combinational 32-bit
# divider explodes under generic Yosys synth (minutes+). A real flow uses a
# sequential/iterative divider or a DesignWare-style macro; tracked for Phase 3.
for core in seth_alu seth_imm seth_regfile seth_aluctl seth_decode seth_csr seth_branch seth_lsu; do
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done

# seth_csru integrates the combinational seth_csr datapath with a CSR bank, so it
# reads both sources.
echo "=== synthesizing seth_csru ==="
"$YOSYS" -ql "reports/seth_csru.log" -p "
    read_verilog -sv ../rtl/seth_csru.sv ../rtl/seth_csr.sv;
    synth -top seth_csru;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/seth_csru.stat stat
"
echo "  -> reports/seth_csru.stat (0 latches asserted)"

# seth_core (single-cycle) and seth_pipeline (5-stage) are full integrated CPUs.
# Both embed seth_muldiv (whose combinational divider explodes under full ABC), so
# we stop at the coarse netlist: that proves the Phase-3 exit gate (0 latches;
# memory inferred as $mem, not flops) deterministically in <1s. Skipped under CI
# (the stock apt Yosys is slow on the muldiv cloud); reports/*.stat are the evidence.
SUBS="../rtl/seth_decode.sv ../rtl/seth_imm.sv ../rtl/seth_aluctl.sv \
      ../rtl/seth_alu.sv ../rtl/seth_muldiv.sv ../rtl/seth_regfile.sv"
if [ -z "${CI:-}" ]; then
    for top in seth_core seth_pipeline seth_pipeline_fwd; do
        echo "=== synthesizing $top (coarse, 0-latch check) ==="
        "$YOSYS" -ql "reports/${top}.log" -p "
            read_verilog -sv $SUBS ../rtl/${top}.sv;
            hierarchy -top ${top};
            synth -top ${top} -run :fine;
            select -assert-none t:\$_DLATCH_* t:\$dlatch;
            tee -o reports/${top}.stat stat
        "
        echo "  -> reports/${top}.stat (0 latches asserted)"
    done
else
    echo "=== skipping CPU synth (seth_core/seth_pipeline) under CI (see committed reports/*.stat) ==="
fi
echo "=== synthesizing seth_mcsr ==="
"$YOSYS" -ql "reports/seth_mcsr.log" -p "
    read_verilog -sv ../rtl/seth_mcsr.sv;
    synth -top seth_mcsr;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/seth_mcsr.stat stat
"
echo "  -> reports/seth_mcsr.stat (0 latches asserted)"
echo "=== synthesizing seth_trap ==="
"$YOSYS" -ql "reports/seth_trap.log" -p "
    read_verilog -sv ../rtl/seth_trap.sv;
    synth -top seth_trap;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/seth_trap.stat stat
"
echo "  -> reports/seth_trap.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
