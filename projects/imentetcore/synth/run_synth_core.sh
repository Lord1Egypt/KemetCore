#!/bin/bash
set -e

# Run Yosys synth for imentet_core
yosys -p "
read_verilog -sv ../rtl/imentet_core.sv ../rtl/imentet_qk_score.sv ../rtl/imentet_mask_add.sv ../rtl/imentet_rowmax_sub.sv ../rtl/imentet_exp.sv ../rtl/imentet_softmax_norm.sv ../rtl/imentet_av_context.sv ../../hapicore/rtl/hapi_fp32_mul.sv ../../hapicore/rtl/hapi_fp32_add.sv ../../hapicore/rtl/hapi_fp32_cmp.sv ../../hapicore/rtl/hapi_fp32_to_int.sv ../../hapicore/rtl/hapi_int_to_fp32.sv ../../hapicore/rtl/hapi_fp32_div.sv
synth -top imentet_core
stat
"
