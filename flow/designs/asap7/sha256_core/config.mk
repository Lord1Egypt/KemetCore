export DESIGN_NICKNAME = sha256_core
export DESIGN_NAME     = sha256_core
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/anubiscore/rtl/sha256_core.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
