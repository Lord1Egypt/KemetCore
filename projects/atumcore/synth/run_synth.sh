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

# atum_vredu is light (adders + comparators, no multipliers) -> full synth always.
echo "=== synthesizing atum_vredu (vector reduction unit) ==="
"$YOSYS" -ql "reports/atum_vredu.log" -p "
    read_verilog -sv ../rtl/atum_vredu.sv;
    synth -top atum_vredu;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vredu.stat stat
"
echo "  -> reports/atum_vredu.stat (0 latches asserted)"

# atum_vregfile + atum_vsetvl are light (regs + a comparator) -> full synth always.
for core in atum_vregfile atum_vsetvl; do
    echo "=== synthesizing $core ==="
    "$YOSYS" -ql "reports/${core}.log" -p "
        read_verilog -sv ../rtl/${core}.sv;
        synth -top ${core};
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/${core}.stat stat
    "
    echo "  -> reports/${core}.stat (0 latches asserted)"
done

# atum_vexec integrates valu + vfpu (fp32 multipliers) + vredu. Like vfpu, full ABC
# mapping is large; under $CI stop at the coarse 0-latch netlist, committed .stat full.
if [ -z "${CI:-}" ]; then
    echo "=== synthesizing atum_vexec (integrated vector execute unit, full) ==="
    "$YOSYS" -ql "reports/atum_vexec.log" -p "
        read_verilog -sv ../rtl/atum_valu.sv ../rtl/atum_vfpu.sv ../rtl/atum_vredu.sv \
            $HAPI/hapi_fp32_mul.sv $HAPI/hapi_fp32_add.sv ../rtl/atum_vexec.sv;
        synth -top atum_vexec;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/atum_vexec.stat stat
    "
else
    echo "=== synthesizing atum_vexec (coarse 0-latch check under CI) ==="
    "$YOSYS" -ql "reports/atum_vexec.log" -p "
        read_verilog -sv ../rtl/atum_valu.sv ../rtl/atum_vfpu.sv ../rtl/atum_vredu.sv \
            $HAPI/hapi_fp32_mul.sv $HAPI/hapi_fp32_add.sv ../rtl/atum_vexec.sv;
        synth -top atum_vexec -run :fine;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        stat
    "
fi
echo "  -> reports/atum_vexec.stat (0 latches asserted)"

# atum_vmask is just a VLMAX-wide comparator array (no multipliers) -> always full.
echo "=== synthesizing atum_vmask (compare-to-mask unit, full) ==="
"$YOSYS" -ql "reports/atum_vmask.log" -p "
    read_verilog -sv ../rtl/atum_vmask.sv;
    synth -top atum_vmask;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vmask.stat stat
"
echo "  -> reports/atum_vmask.stat (0 latches asserted)"

# atum_vmlogic is trivial mask bit-logic (no arithmetic) -> always full.
echo "=== synthesizing atum_vmlogic (mask logical unit, full) ==="
"$YOSYS" -ql "reports/atum_vmlogic.log" -p "
    read_verilog -sv ../rtl/atum_vmlogic.sv;
    synth -top atum_vmlogic;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vmlogic.stat stat
"
echo "  -> reports/atum_vmlogic.stat (0 latches asserted)"

# atum_vmpopc is a small mask reduction (adders + priority encode) -> always full.
echo "=== synthesizing atum_vmpopc (mask reduction unit, full) ==="
"$YOSYS" -ql "reports/atum_vmpopc.log" -p "
    read_verilog -sv ../rtl/atum_vmpopc.sv;
    synth -top atum_vmpopc;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vmpopc.stat stat
"
echo "  -> reports/atum_vmpopc.stat (0 latches asserted)"

# atum_viota is a small prefix-sum / index generator (adders) -> always full.
echo "=== synthesizing atum_viota (mask iota / index unit, full) ==="
"$YOSYS" -ql "reports/atum_viota.log" -p "
    read_verilog -sv ../rtl/atum_viota.sv;
    synth -top atum_viota;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_viota.stat stat
"
echo "  -> reports/atum_viota.stat (0 latches asserted)"

# atum_vcompress is a mask-driven gather (mux tree, no arithmetic) -> always full.
echo "=== synthesizing atum_vcompress (stream compaction unit, full) ==="
"$YOSYS" -ql "reports/atum_vcompress.log" -p "
    read_verilog -sv ../rtl/atum_vcompress.sv;
    synth -top atum_vcompress;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vcompress.stat stat
"
echo "  -> reports/atum_vcompress.stat (0 latches asserted)"

# atum_vrgather is a VLMAX:1-per-lane mux tree (no arithmetic) -> always full.
echo "=== synthesizing atum_vrgather (register gather unit, full) ==="
"$YOSYS" -ql "reports/atum_vrgather.log" -p "
    read_verilog -sv ../rtl/atum_vrgather.sv;
    synth -top atum_vrgather;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vrgather.stat stat
"
echo "  -> reports/atum_vrgather.stat (0 latches asserted)"

# atum_vslide is a VLMAX:1-per-lane mux + offset compares (no multipliers) -> full.
echo "=== synthesizing atum_vslide (vector slide unit, full) ==="
"$YOSYS" -ql "reports/atum_vslide.log" -p "
    read_verilog -sv ../rtl/atum_vslide.sv;
    synth -top atum_vslide;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vslide.stat stat
"
echo "  -> reports/atum_vslide.stat (0 latches asserted)"

# atum_vmerge is a per-lane 2:1 mux (no arithmetic) -> always full.
echo "=== synthesizing atum_vmerge (vector merge / select unit, full) ==="
"$YOSYS" -ql "reports/atum_vmerge.log" -p "
    read_verilog -sv ../rtl/atum_vmerge.sv;
    synth -top atum_vmerge;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vmerge.stat stat
"
echo "  -> reports/atum_vmerge.stat (0 latches asserted)"

# atum_vfsgnj is pure fp bit manipulation (no arithmetic) -> always full.
echo "=== synthesizing atum_vfsgnj (fp sign-injection unit, full) ==="
"$YOSYS" -ql "reports/atum_vfsgnj.log" -p "
    read_verilog -sv ../rtl/atum_vfsgnj.sv;
    synth -top atum_vfsgnj;
    select -assert-none t:\$_DLATCH_* t:\$dlatch;
    tee -o reports/atum_vfsgnj.stat stat
"
echo "  -> reports/atum_vfsgnj.stat (0 latches asserted)"

# atum_vcore embeds the whole vexec datapath (fp32 multipliers) + vreg array. Full
# ABC mapping is large; under $CI stop at the coarse 0-latch netlist, committed .stat full.
VC_SRCS="../rtl/atum_valu.sv ../rtl/atum_vfpu.sv ../rtl/atum_vredu.sv \
         $HAPI/hapi_fp32_mul.sv $HAPI/hapi_fp32_add.sv ../rtl/atum_vexec.sv \
         ../rtl/atum_vregfile.sv ../rtl/atum_vsetvl.sv ../rtl/atum_vcore.sv"
if [ -z "${CI:-}" ]; then
    echo "=== synthesizing atum_vcore (single-cycle vector core, full) ==="
    "$YOSYS" -ql "reports/atum_vcore.log" -p "
        read_verilog -sv $VC_SRCS;
        synth -top atum_vcore;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        tee -o reports/atum_vcore.stat stat
    "
else
    echo "=== synthesizing atum_vcore (coarse 0-latch check under CI) ==="
    "$YOSYS" -ql "reports/atum_vcore.log" -p "
        read_verilog -sv $VC_SRCS;
        hierarchy -top atum_vcore;
        synth -top atum_vcore -run :fine;
        select -assert-none t:\$_DLATCH_* t:\$dlatch;
        stat
    "
fi
echo "  -> reports/atum_vcore.stat (0 latches asserted)"
echo "ALL SYNTHESIZED ✅ (no latches)"
