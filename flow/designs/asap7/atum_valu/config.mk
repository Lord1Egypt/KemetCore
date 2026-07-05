export DESIGN_NICKNAME = atum_valu
export DESIGN_NAME     = atum_valu_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_valu_p4top.sv $(KEMETCORE)/projects/atumcore/rtl/atum_valu.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
