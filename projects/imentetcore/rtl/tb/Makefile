# cocotb + Verilator testbenches for ImentetCore.
#   make CORE=qkscore  (default) -> imentet_qk_score fp32 scaled dot-product score (+ hapi fp32)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= qkscore

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# The Imentet primitives instantiate the verified HapiCore fp32 blocks.
ifeq ($(CORE),qkscore)
VERILOG_SOURCES = $(PWD)/../imentet_qk_score.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = imentet_qk_score
MODULE   = test_qk_score
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

include $(shell cocotb-config --makefiles)/Makefile.sim
