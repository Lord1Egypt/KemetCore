export DESIGN_NICKNAME = neith_butterfly
export DESIGN_NAME     = neith_butterfly_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/neithcore/rtl/neith_butterfly_p4top.sv \
                         $(KEMETCORE)/projects/neithcore/rtl/neith_butterfly.sv \
                         $(KEMETCORE)/projects/neithcore/rtl/neith_modmul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 30
export PLACE_DENSITY     = 0.40
