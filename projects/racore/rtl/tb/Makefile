# cocotb + Verilator testbenches for RaCore.
#   make CORE=kai  (default)  -> ra_kai_regs (KAI MMIO register block)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= kai
PWD := $(shell pwd)

VERILOG_SOURCES = $(PWD)/../ra_kai_regs.sv
TOPLEVEL = ra_kai_regs
MODULE   = test_kai_regs

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
include $(shell cocotb-config --makefiles)/Makefile.sim
