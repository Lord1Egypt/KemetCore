export DESIGN_NICKNAME = neith_modmul
export DESIGN_NAME     = neith_modmul_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/neithcore/rtl/neith_modmul_p4top.sv \
                         $(KEMETCORE)/projects/neithcore/rtl/neith_modmul.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc

export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.65
export CORE_ASPECT_RATIO = 1
