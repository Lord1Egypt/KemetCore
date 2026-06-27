# cocotb + Verilator testbenches for AnubisCore.
#   make CORE=sha256   (default)   -> sha256_core
#   make CORE=sha3                 -> sha3_256_core
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= sha256

PWD := $(shell pwd)

ifeq ($(CORE),sha3)
  VERILOG_SOURCES = $(PWD)/../sha3_256_core.sv
  TOPLEVEL = sha3_256_core
  MODULE   = test_sha3
else
  VERILOG_SOURCES = $(PWD)/../sha256_core.sv
  TOPLEVEL = sha256_core
  MODULE   = test_sha256
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
