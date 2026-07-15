export DESIGN_NICKNAME = sobek_lerp
export DESIGN_NAME     = sobek_lerp_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_lerp_p4top.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_lerp.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 15
export PLACE_DENSITY     = 0.30
