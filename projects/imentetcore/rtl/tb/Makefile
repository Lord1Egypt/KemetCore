# cocotb + Verilator testbenches for ImentetCore.
#   make CORE=qkscore  (default) -> imentet_qk_score fp32 scaled dot-product score (+ hapi fp32)
#   make CORE=av       -> imentet_av_context fp32 weighted value accumulation (+ hapi fp32)
#   make CORE=rowmax   -> imentet_rowmax_sub softmax stabilization x-max(x) (+ hapi add)
#   make CORE=norm     -> imentet_softmax_norm softmax normalize e/sum(e) (+ hapi add/div/mul)
#   make CORE=mask     -> imentet_mask_add additive attention mask x+m (+ hapi add)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= qkscore

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# The Imentet primitives instantiate the verified HapiCore fp32 blocks.
ifeq ($(CORE),exp)
VERILOG_SOURCES = $(PWD)/../imentet_exp.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv $(HAPI)/hapi_fp32_cmp.sv $(HAPI)/hapi_fp32_to_int.sv $(HAPI)/hapi_int_to_fp32.sv
TOPLEVEL = imentet_exp
MODULE   = test_exp
else ifeq ($(CORE),mask)
VERILOG_SOURCES = $(PWD)/../imentet_mask_add.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = imentet_mask_add
MODULE   = test_mask_add
else ifeq ($(CORE),norm)
VERILOG_SOURCES = $(PWD)/../imentet_softmax_norm.sv $(HAPI)/hapi_fp32_add.sv $(HAPI)/hapi_fp32_div.sv $(HAPI)/hapi_fp32_mul.sv
TOPLEVEL = imentet_softmax_norm
MODULE   = test_softmax_norm
else ifeq ($(CORE),rowmax)
VERILOG_SOURCES = $(PWD)/../imentet_rowmax_sub.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = imentet_rowmax_sub
MODULE   = test_rowmax_sub
else ifeq ($(CORE),av)
VERILOG_SOURCES = $(PWD)/../imentet_av_context.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = imentet_av_context
MODULE   = test_av_context
else ifeq ($(CORE),qkscore)
VERILOG_SOURCES = $(PWD)/../imentet_qk_score.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = imentet_qk_score
MODULE   = test_qk_score
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

include $(shell cocotb-config --makefiles)/Makefile.sim
