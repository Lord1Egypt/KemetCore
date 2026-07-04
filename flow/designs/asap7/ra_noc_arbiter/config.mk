export DESIGN_NICKNAME = ra_noc_arbiter
export DESIGN_NAME     = ra_noc_arbiter
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/racore/rtl/ra_noc_arbiter.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
