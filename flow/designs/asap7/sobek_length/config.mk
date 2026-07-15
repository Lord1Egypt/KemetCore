export DESIGN_NICKNAME = sobek_length
export DESIGN_NAME     = sobek_length_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_length_p4top.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_length.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_sqrt.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 10
export PLACE_DENSITY     = 0.25
