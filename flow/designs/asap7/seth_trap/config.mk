export DESIGN_NICKNAME = seth_trap
export DESIGN_NAME     = seth_trap_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sethcore/rtl/seth_trap_p4top.sv $(KEMETCORE)/projects/sethcore/rtl/seth_trap.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
