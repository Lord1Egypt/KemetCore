export DESIGN_NICKNAME = seth_imm
export DESIGN_NAME     = seth_imm_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/sethcore/rtl/seth_imm_p4top.sv $(KEMETCORE)/projects/sethcore/rtl/seth_imm.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
