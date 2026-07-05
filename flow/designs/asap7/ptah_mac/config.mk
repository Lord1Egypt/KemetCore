export DESIGN_NICKNAME = ptah_mac
export DESIGN_NAME     = ptah_mac
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/ptahconv/rtl/ptah_mac.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
