# cocotb + Verilator testbenches for SobekCore.
#   make CORE=dot3  (default)  -> sobek_dot3 fp32 3-element dot product (+ hapi fp32)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= dot3

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# sobek_dot3 instantiates the verified HapiCore fp32 primitives, so they compile in.
ifeq ($(CORE),dot3)
VERILOG_SOURCES = $(PWD)/../sobek_dot3.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_dot3
MODULE   = test_dot3
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
