# cocotb + Verilator testbenches for the HapiCore FPU datapath.
#   make CORE=mul     (default)   -> hapi_bf16_mul
#   make CORE=add                 -> hapi_bf16_add
#   make CORE=fp32add             -> hapi_fp32_add
#   make CORE=fp32mul             -> hapi_fp32_mul
#   make CORE=fp16mul             -> hapi_fp16_mul
#   make CORE=fp16add             -> hapi_fp16_add
#   make CORE=fp32fma             -> hapi_fp32_fma
#   make CORE=bf16fma             -> hapi_bf16_fma (hapi_fma_core)
#   make CORE=fp16fma             -> hapi_fp16_fma (hapi_fma_core)
#   make CORE=fp32div             -> hapi_fp32_div
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= mul

PWD := $(shell pwd)

ifeq ($(CORE),add)
  VERILOG_SOURCES = $(PWD)/../hapi_bf16_add.sv
  TOPLEVEL = hapi_bf16_add
  MODULE   = test_bf16_add
else ifeq ($(CORE),fp32add)
  VERILOG_SOURCES = $(PWD)/../hapi_fp32_add.sv
  TOPLEVEL = hapi_fp32_add
  MODULE   = test_fp32_add
else ifeq ($(CORE),fp32mul)
  VERILOG_SOURCES = $(PWD)/../hapi_fp32_mul.sv
  TOPLEVEL = hapi_fp32_mul
  MODULE   = test_fp32_mul
else ifeq ($(CORE),fp16mul)
  VERILOG_SOURCES = $(PWD)/../hapi_fp16_mul.sv
  TOPLEVEL = hapi_fp16_mul
  MODULE   = test_fp16_mul
else ifeq ($(CORE),fp16add)
  VERILOG_SOURCES = $(PWD)/../hapi_fp16_add.sv
  TOPLEVEL = hapi_fp16_add
  MODULE   = test_fp16_add
else ifeq ($(CORE),fp32fma)
  VERILOG_SOURCES = $(PWD)/../hapi_fp32_fma.sv
  TOPLEVEL = hapi_fp32_fma
  MODULE   = test_fp32_fma
else ifeq ($(CORE),bf16fma)
  VERILOG_SOURCES = $(PWD)/../hapi_fma_core.sv
  TOPLEVEL = hapi_bf16_fma
  MODULE   = test_bf16_fma
else ifeq ($(CORE),fp16fma)
  VERILOG_SOURCES = $(PWD)/../hapi_fma_core.sv
  TOPLEVEL = hapi_fp16_fma
  MODULE   = test_fp16_fma
else ifeq ($(CORE),fp32div)
  VERILOG_SOURCES = $(PWD)/../hapi_fp32_div.sv
  TOPLEVEL = hapi_fp32_div
  MODULE   = test_fp32_div
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
