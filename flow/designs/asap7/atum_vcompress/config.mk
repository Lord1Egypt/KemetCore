export DESIGN_NICKNAME = atum_vcompress
export DESIGN_NAME     = atum_vcompress_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vcompress_p4top.sv \
                         $(KEMETCORE)/projects/atumcore/rtl/atum_vcompress.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 20
export PLACE_DENSITY     = 0.40
