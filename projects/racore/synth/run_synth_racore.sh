#!/bin/bash
set -e
yosys -p "
read_verilog -sv ../rtl/racore_lite.sv ../rtl/ra_noc_xbar.sv ../rtl/ra_noc_arbiter.sv ../rtl/ra_scratchpad.sv ../../sethcore/rtl/seth_pipeline_fwd.sv ../../sethcore/rtl/seth_alu.sv ../../sethcore/rtl/seth_muldiv_seq.sv ../../sethcore/rtl/seth_regfile.sv
synth -top racore_lite
stat
"
