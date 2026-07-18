export DESIGN_NICKNAME = sobek_distance
export DESIGN_NAME     = sobek_distance_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_distance_p4top.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_distance.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_length.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_dot3.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_sqrt.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc

export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.60
export CORE_ASPECT_RATIO = 1
