# cocotb + Verilator testbenches for RaCore.
#   make CORE=kai  (default)  -> ra_kai_regs (KAI MMIO register block)
#   make CORE=noc             -> ra_noc_arbiter (round-robin NoC arbiter)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= kai
PWD := $(shell pwd)

ifeq ($(CORE),noc)
  VERILOG_SOURCES = $(PWD)/../ra_noc_arbiter.sv
  TOPLEVEL = ra_noc_arbiter
  MODULE   = test_noc
else
VERILOG_SOURCES = $(PWD)/../ra_kai_regs.sv
TOPLEVEL = ra_kai_regs
MODULE   = test_kai_regs
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
include $(shell cocotb-config --makefiles)/Makefile.sim
