export DESIGN_NICKNAME = atum_viota
export DESIGN_NAME     = atum_viota_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_viota_p4top.sv \
                         $(KEMETCORE)/projects/atumcore/rtl/atum_viota.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.50
