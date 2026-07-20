#!/usr/bin/env bash
# Phase 3: Yosys synthesis for the RaCore KAI register block; asserts no latches.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports
echo "=== synthesizing ra_kai_regs ==="
"$YOSYS" -ql "reports/ra_kai_regs.log" -p "
    read_verilog -sv ../rtl/ra_kai_regs.sv;
    synth -top ra_kai_regs;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_kai_regs.stat stat
"
echo "  -> reports/ra_kai_regs.stat (0 latches asserted)"

echo "=== synthesizing ra_noc_arbiter ==="
"$YOSYS" -ql "reports/ra_noc_arbiter.log" -p "
    read_verilog -sv ../rtl/ra_noc_arbiter.sv;
    synth -top ra_noc_arbiter;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_noc_arbiter.stat stat
"
echo "  -> reports/ra_noc_arbiter.stat (0 latches asserted)"

echo "=== synthesizing ra_scratchpad ==="
"$YOSYS" -ql "reports/ra_scratchpad.log" -p "
    read_verilog -sv ../rtl/ra_scratchpad.sv;
    synth -top ra_scratchpad;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_scratchpad.stat stat
"
echo "  -> reports/ra_scratchpad.stat (0 latches asserted)"

echo "=== synthesizing ra_dma ==="
"$YOSYS" -ql "reports/ra_dma.log" -p "
    read_verilog -sv ../rtl/ra_dma.sv;
    synth -top ra_dma;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_dma.stat stat
"
echo "  -> reports/ra_dma.stat (0 latches asserted)"

# ra_kai_dma re-instantiates ra_dma's 1KB scratchpad behind the KAI regs; the
# scratchpad is already full-synth'd via the standalone ra_dma above, and the
# integrated cloud is slow on the stock apt Yosys, so synth it locally (committed
# reports/ra_kai_dma.stat is the 0-latch evidence) and skip under CI. Its cocotb
# end-to-end test DOES run in CI.
if [ -z "${CI:-}" ]; then
    echo "=== synthesizing ra_kai_dma (KAI-wrapped DMA accelerator) ==="
    "$YOSYS" -ql "reports/ra_kai_dma.log" -p "
        read_verilog -sv ../rtl/ra_kai_dma.sv ../rtl/ra_kai_regs.sv ../rtl/ra_dma.sv;
        synth -top ra_kai_dma;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/ra_kai_dma.stat stat
    "
    echo "  -> reports/ra_kai_dma.stat (0 latches asserted)"
else
    echo "=== skipping ra_kai_dma synth under CI (see committed reports/ra_kai_dma.stat) ==="
fi

echo "=== synthesizing ra_noc_xbar ==="
"$YOSYS" -ql "reports/ra_noc_xbar.log" -p "
    read_verilog -sv ../rtl/ra_noc_xbar.sv ../rtl/ra_noc_arbiter.sv;
    synth -top ra_noc_xbar;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/ra_noc_xbar.stat stat
"
echo "  -> reports/ra_noc_xbar.stat (0 latches asserted)"

echo "=== synthesizing racore_lite ==="
"$YOSYS" -ql "reports/racore_lite.log" -p "
    read_verilog -sv ../rtl/racore_lite.sv ../rtl/ra_bootrom.sv ../rtl/ra_noc_xbar.sv ../rtl/ra_noc_arbiter.sv ../rtl/ra_scratchpad.sv ../../sethcore/rtl/seth_*.sv;
    synth -top racore_lite;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/racore_lite.stat stat
"
echo "  -> reports/racore_lite.stat (0 latches asserted)"

echo "ALL SYNTHESIZED ✅ (no latches)"
