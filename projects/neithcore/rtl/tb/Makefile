# cocotb + Verilator testbenches for NeithCore NTT primitives.
#   make CORE=modmul   (default)   -> neith_modmul
#   make CORE=butterfly            -> neith_butterfly (+ neith_modmul)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= modmul

PWD := $(shell pwd)

ifeq ($(CORE),butterfly)
  VERILOG_SOURCES = $(PWD)/../neith_butterfly.sv $(PWD)/../neith_modmul.sv
  TOPLEVEL = neith_butterfly
  MODULE   = test_butterfly
else
  VERILOG_SOURCES = $(PWD)/../neith_modmul.sv
  TOPLEVEL = neith_modmul
  MODULE   = test_modmul
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
