export DESIGN_NICKNAME = hapi_bf16_add
export DESIGN_NAME     = hapi_bf16_add_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/hapicore/rtl/hapi_bf16_add_p4top.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_bf16_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
