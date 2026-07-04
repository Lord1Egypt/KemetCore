# KemetCore — ASAP7 harden of bast_mac (BF16 multiply / FP32 accumulate PE).
# First KemetCore Phase-4 (P&R -> GDSII) design, run through the same ORFS
# container PtahCore uses. Small sequential block: one accumulator register +
# the combinational hapi_bf16_mul / hapi_fp32_add it composes.
export DESIGN_NICKNAME = bast_mac
export DESIGN_NAME     = bast_mac
export PLATFORM        = asap7

export VERILOG_FILES = \
  $(KEMETCORE)/projects/bastcore/rtl/bast_mac.sv \
  $(KEMETCORE)/projects/hapicore/rtl/hapi_bf16_mul.sv \
  $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv

export SDC_FILE = $(dir $(DESIGN_CONFIG))/constraint.sdc

# small block -> generous utilisation, let the flow pick the die
export CORE_UTILIZATION   = 35
export PLACE_DENSITY      = 0.55
export CORE_ASPECT_RATIO  = 1
