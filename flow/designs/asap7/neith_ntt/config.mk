export DESIGN_NICKNAME = neith_ntt
export DESIGN_NAME     = neith_ntt
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/neithcore/rtl/neith_ntt.sv $(KEMETCORE)/projects/neithcore/rtl/neith_butterfly.sv $(KEMETCORE)/projects/neithcore/rtl/neith_modmul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
