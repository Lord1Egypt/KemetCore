export DESIGN_NICKNAME = atum_vimac
export DESIGN_NAME     = atum_vimac_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vimac_p4top.sv $(KEMETCORE)/projects/atumcore/rtl/atum_vimac.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.50
export CORE_ASPECT_RATIO = 1
