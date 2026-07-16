export DESIGN_NICKNAME = hapi_fp32_minmax
export DESIGN_NAME     = hapi_fp32_minmax_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_minmax_p4top.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_minmax.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 25
export PLACE_DENSITY     = 0.45
export CORE_ASPECT_RATIO = 1
