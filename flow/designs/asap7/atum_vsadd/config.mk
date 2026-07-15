export DESIGN_NICKNAME = atum_vsadd
export DESIGN_NAME     = atum_vsadd_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vsadd_p4top.sv \
                         $(KEMETCORE)/projects/atumcore/rtl/atum_vsadd.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 15
export PLACE_DENSITY     = 0.35
