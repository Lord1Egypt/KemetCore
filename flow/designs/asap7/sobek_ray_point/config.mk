export DESIGN_NICKNAME = sobek_ray_point
export DESIGN_NAME     = sobek_ray_point_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sobekcore/rtl/sobek_ray_point_p4top.sv \
                         $(KEMETCORE)/projects/sobekcore/rtl/sobek_ray_point.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 20
export PLACE_DENSITY     = 0.40
