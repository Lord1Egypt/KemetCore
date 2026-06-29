# cocotb + Verilator testbenches for PtahConv.
#   make CORE=mac  (default)  -> ptah_mac fp32 MAC PE (+ hapi_fp32_mul, hapi_fp32_add)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= mac

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# ptah_mac instantiates the verified HapiCore fp32 primitives, so they are compiled in.
VERILOG_SOURCES = $(PWD)/../ptah_mac.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = ptah_mac
MODULE   = test_mac

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
