export DESIGN_NICKNAME = atum_vsetvl
export DESIGN_NAME     = atum_vsetvl_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vsetvl_p4top.sv $(KEMETCORE)/projects/atumcore/rtl/atum_vsetvl.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 25
export PLACE_DENSITY     = 0.45
export CORE_ASPECT_RATIO = 1
