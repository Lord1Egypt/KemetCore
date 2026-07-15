export DESIGN_NICKNAME = sobek_reflect
export DESIGN_NAME     = sobek_reflect_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_reflect_p4top.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_reflect.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
