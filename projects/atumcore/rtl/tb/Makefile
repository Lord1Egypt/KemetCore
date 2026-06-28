# cocotb + Verilator testbenches for AtumCore (RVV).
#   make CORE=valu   (default)   -> atum_valu (vector integer ALU lane array)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= valu

PWD := $(shell pwd)

ifeq ($(CORE),valu)
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv
  TOPLEVEL = atum_valu
  MODULE   = test_valu
else
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv
  TOPLEVEL = atum_valu
  MODULE   = test_valu
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# If cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
