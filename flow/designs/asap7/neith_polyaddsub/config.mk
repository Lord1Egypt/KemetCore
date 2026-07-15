export DESIGN_NICKNAME = neith_polyaddsub
export DESIGN_NAME     = neith_polyaddsub_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/neithcore/rtl/neith_polyaddsub_p4top.sv \
                         $(KEMETCORE)/projects/neithcore/rtl/neith_polyaddsub.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.50
