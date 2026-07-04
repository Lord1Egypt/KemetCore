# cocotb + Verilator testbenches for GebCore.
#   make CORE=spmac   (default)   -> geb_spmac (+ HapiCore hapi_fp32_mul, hapi_fp32_add)
#   make CORE=prune               -> geb_prune (2:4 sparsity pruner)
#   make CORE=compress            -> geb_compress (2:4 metadata compression)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= spmac

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

ifeq ($(CORE),prune)
  VERILOG_SOURCES = $(PWD)/../geb_prune.sv
  TOPLEVEL = geb_prune
  MODULE   = test_prune
else ifeq ($(CORE),compress)
  VERILOG_SOURCES = $(PWD)/../geb_compress.sv
  TOPLEVEL = geb_compress
  MODULE   = test_compress
else
# geb_spmac instantiates the verified HapiCore fp32 primitives, so they are compiled in.
VERILOG_SOURCES = $(PWD)/../geb_spmac.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = geb_spmac
MODULE   = test_spmac
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
