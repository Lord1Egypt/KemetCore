export DESIGN_NICKNAME = hapi_fp32_to_int
export DESIGN_NAME     = hapi_fp32_to_int_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_to_int_p4top.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_to_int.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 20
export PLACE_DENSITY     = 0.40
