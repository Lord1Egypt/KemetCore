export DESIGN_NICKNAME = hapi_fp32_div
export DESIGN_NAME     = hapi_fp32_div_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_div_p4top.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_div.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc

export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.65
export CORE_ASPECT_RATIO = 1
