export DESIGN_NICKNAME = imentet_av_context
export DESIGN_NAME     = imentet_av_context_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/imentetcore/rtl/imentet_av_context_p4top.sv \
                         $(KEMETCORE)/projects/imentetcore/rtl/imentet_av_context.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv \
                         $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc

export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.65
export CORE_ASPECT_RATIO = 1
