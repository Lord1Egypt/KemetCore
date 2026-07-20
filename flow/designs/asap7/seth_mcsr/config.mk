export DESIGN_NICKNAME = seth_mcsr
export DESIGN_NAME     = seth_mcsr_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sethcore/rtl/seth_mcsr_p4top.sv $(KEMETCORE)/projects/sethcore/rtl/seth_mcsr.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
