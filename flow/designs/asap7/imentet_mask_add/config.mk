export DESIGN_NICKNAME = imentet_mask_add
export DESIGN_NAME     = imentet_mask_add_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/imentetcore/rtl/imentet_mask_add_p4top.sv $(KEMETCORE)/projects/imentetcore/rtl/imentet_mask_add.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 15
export PLACE_DENSITY     = 0.35
