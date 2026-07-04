# cocotb + Verilator testbenches for SobekCore.
#   make CORE=dot3  (default)  -> sobek_dot3 fp32 3-element dot product (+ hapi fp32)
#   make CORE=cross            -> sobek_cross fp32 3-D cross product (+ hapi fp32)
#   make CORE=scale            -> sobek_scale fp32 scalar-vector product (+ hapi fp32)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= dot3

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# The Sobek primitives instantiate the verified HapiCore fp32 blocks, so they compile in.
ifeq ($(CORE),cross)
VERILOG_SOURCES = $(PWD)/../sobek_cross.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_cross
MODULE   = test_cross
else ifeq ($(CORE),scale)
VERILOG_SOURCES = $(PWD)/../sobek_scale.sv $(HAPI)/hapi_fp32_mul.sv
TOPLEVEL = sobek_scale
MODULE   = test_scale
else ifeq ($(CORE),dot3)
VERILOG_SOURCES = $(PWD)/../sobek_dot3.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_dot3
MODULE   = test_dot3
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
