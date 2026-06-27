# cocotb + Verilator testbenches for HapiCore bf16 datapath.
#   make CORE=mul   (default)   -> hapi_bf16_mul
#   make CORE=add               -> hapi_bf16_add
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= mul

PWD := $(shell pwd)

ifeq ($(CORE),add)
  VERILOG_SOURCES = $(PWD)/../hapi_bf16_add.sv
  TOPLEVEL = hapi_bf16_add
  MODULE   = test_bf16_add
else
  VERILOG_SOURCES = $(PWD)/../hapi_bf16_mul.sv
  TOPLEVEL = hapi_bf16_mul
  MODULE   = test_bf16_mul
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
