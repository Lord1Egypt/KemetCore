export DESIGN_NICKNAME = geb_spmac
export DESIGN_NAME     = geb_spmac
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/gebcore/rtl/geb_spmac.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
