export DESIGN_NICKNAME = imentet_exp
export DESIGN_NAME     = imentet_exp_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/imentetcore/rtl/imentet_exp_p4top.sv \
                         $(KEMETCORE)/projects/imentetcore/rtl/imentet_exp.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_cmp.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_to_int.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_int_to_fp32.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc

export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.60
export CORE_ASPECT_RATIO = 1
