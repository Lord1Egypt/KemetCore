# cocotb + Verilator testbench for the GebCore 2:4 sparse-MAC cell.
#   make CORE=spmac   (default)   -> geb_spmac (+ HapiCore hapi_fp32_mul, hapi_fp32_add)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= spmac

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# geb_spmac instantiates the verified HapiCore fp32 primitives, so they are compiled in.
VERILOG_SOURCES = $(PWD)/../geb_spmac.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = geb_spmac
MODULE   = test_spmac

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
