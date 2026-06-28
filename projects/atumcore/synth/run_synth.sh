#!/usr/bin/env bash
# Phase 3: generic Yosys synthesis for the AtumCore RVV primitives.
# Reports gate/cell counts and ASSERTS there are no latches (a Phase 3 exit gate).
# Reports are written to reports/<core>.stat and committed as synthesis evidence.
set -euo pipefail
cd "$(dirname "$0")"
YOSYS="${YOSYS:-$HOME/miniconda3/envs/eda/bin/yosys}"
mkdir -p reports

# atum_valu embeds VLMAX (=8) parallel 32-bit multipliers. Full ABC gate-mapping is
# ~33K cells locally (fast on conda Yosys); the stock apt Yosys on the CI runner is
# slow mapping that many multipliers, so under $CI we stop at the coarse netlist
# (synth -run :fine): that still proves the Phase-3 exit gate (0 latches; multiplies
# inferred as $mul, not flops) in <1s. The committed reports/atum_valu.stat (full
# gate-level) is the evidence.
if [ -z "${CI:-}" ]; then
    echo "=== synthesizing atum_valu (vector integer ALU lane array, full) ==="
    "$YOSYS" -ql "reports/atum_valu.log" -p "
        read_verilog -sv ../rtl/atum_valu.sv;
        synth -top atum_valu;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/atum_valu.stat stat
    "
else
    echo "=== synthesizing atum_valu (coarse 0-latch check under CI) ==="
    "$YOSYS" -ql "reports/atum_valu.log" -p "
        read_verilog -sv ../rtl/atum_valu.sv;
        synth -top atum_valu -run :fine;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        stat
    "
fi
echo "  -> reports/atum_valu.stat (0 latches asserted)"

# atum_vfpu embeds VLMAX fp32 mul + fp32 add cores (each with a wide mantissa
# multiplier). Full ABC gate-mapping is large; under $CI we stop at the coarse
# netlist (0 latches; arithmetic inferred, not flops). Committed .stat is full.
HAPI="../../hapicore/rtl"
if [ -z "${CI:-}" ]; then
    echo "=== synthesizing atum_vfpu (fp32 vector lane, full) ==="
    "$YOSYS" -ql "reports/atum_vfpu.log" -p "
        read_verilog -sv $HAPI/hapi_fp32_mul.sv $HAPI/hapi_fp32_add.sv ../rtl/atum_vfpu.sv;
        synth -top atum_vfpu;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/atum_vfpu.stat stat
    "
else
    echo "=== synthesizing atum_vfpu (coarse 0-latch check under CI) ==="
    "$YOSYS" -ql "reports/atum_vfpu.log" -p "
        read_verilog -sv $HAPI/hapi_fp32_mul.sv $HAPI/hapi_fp32_add.sv ../rtl/atum_vfpu.sv;
        synth -top atum_vfpu -run :fine;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        stat
    "
fi
echo "  -> reports/atum_vfpu.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
