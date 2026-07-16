export DESIGN_NICKNAME = hapi_fp16_cmp
export DESIGN_NAME     = hapi_fp16_cmp_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/hapicore/rtl/hapi_fp16_cmp_p4top.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp16_cmp.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 25
export PLACE_DENSITY     = 0.45
export CORE_ASPECT_RATIO = 1
