export DESIGN_NICKNAME = imentet_qk_score
export DESIGN_NAME     = imentet_qk_score_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/imentetcore/rtl/imentet_qk_score_p4top.sv $(KEMETCORE)/projects/imentetcore/rtl/imentet_qk_score.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
