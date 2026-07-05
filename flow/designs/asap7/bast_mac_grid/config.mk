export DESIGN_NICKNAME = bast_mac_grid
export DESIGN_NAME     = bast_mac_grid
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/bastcore/rtl/bast_mac_grid.sv $(KEMETCORE)/projects/bastcore/rtl/bast_mac.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_bf16_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
