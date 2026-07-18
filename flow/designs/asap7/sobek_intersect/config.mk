export DESIGN_NICKNAME = sobek_intersect
export DESIGN_NAME     = sobek_intersect_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_intersect_p4top.sv $(KEMETCORE)/projects/sobekcore/rtl/sobek_intersect.sv $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3.sv $(KEMETCORE)/projects/sobekcore/rtl/sobek_cross.sv $(KEMETCORE)/projects/sobekcore/rtl/sobek_recip.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_cmp.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_div.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.60
export CORE_ASPECT_RATIO = 1
