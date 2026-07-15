export DESIGN_NICKNAME = atum_vmask
export DESIGN_NAME     = atum_vmask_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vmask_p4top.sv \
                         $(KEMETCORE)/projects/atumcore/rtl/atum_vmask.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.50
