export DESIGN_NICKNAME = sobek_dot3
export DESIGN_NAME     = sobek_dot3_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3_p4top.sv $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
