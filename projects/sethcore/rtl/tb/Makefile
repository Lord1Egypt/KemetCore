# cocotb + Verilator testbenches for SethCore.
#   make CORE=alu      (default) -> seth_alu
#   make CORE=muldiv             -> seth_muldiv
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= alu
PWD := $(shell pwd)

ifeq ($(CORE),muldiv)
  VERILOG_SOURCES = $(PWD)/../seth_muldiv.sv
  TOPLEVEL = seth_muldiv
  MODULE   = test_muldiv
else
  VERILOG_SOURCES = $(PWD)/../seth_alu.sv
  TOPLEVEL = seth_alu
  MODULE   = test_alu
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
# If cocotb and Verilator use different Pythons, run via ./run_sim.sh
include $(shell cocotb-config --makefiles)/Makefile.sim
