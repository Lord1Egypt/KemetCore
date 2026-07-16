export DESIGN_NICKNAME = ptah_maxpool
export DESIGN_NAME     = ptah_maxpool_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/ptahconv/rtl/ptah_maxpool_p4top.sv $(KEMETCORE)/projects/ptahconv/rtl/ptah_maxpool.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.65
