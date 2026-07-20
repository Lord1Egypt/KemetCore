export DESIGN_NICKNAME   = sha3_256_core
export DESIGN_NAME       = sha3_256_core_p4top
export PLATFORM          = asap7
export VERILOG_FILES     = $(KEMETCORE)/projects/anubiscore/rtl/sha3_256_core_p4top.sv $(KEMETCORE)/projects/anubiscore/rtl/sha3_256_core.sv
export SDC_FILE          = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
