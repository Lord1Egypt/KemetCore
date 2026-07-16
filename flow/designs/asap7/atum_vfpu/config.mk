export DESIGN_NICKNAME = atum_vfpu
export DESIGN_NAME     = atum_vfpu_p4top
export PLATFORM        = asap7
export VERILOG_FILES   = $(KEMETCORE)/projects/atumcore/rtl/atum_vfpu_p4top.sv $(KEMETCORE)/projects/atumcore/rtl/atum_vfpu.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_mul.sv $(KEMETCORE)/projects/hapicore/rtl/hapi_fp32_add.sv
export SDC_FILE        = $(dir $(DESIGN_CONFIG))/constraint.sdc
export CORE_UTILIZATION  = 40
export PLACE_DENSITY     = 0.60
export CORE_ASPECT_RATIO = 1
