export DESIGN_NICKNAME = ptah_bias_relu
export DESIGN_NAME     = ptah_bias_relu_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/ptahconv/rtl/ptah_bias_relu_p4top.sv $(KEMETCORE)/projects/ptahconv/rtl/ptah_bias_relu.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 35
export PLACE_DENSITY     = 0.55
export CORE_ASPECT_RATIO = 1
