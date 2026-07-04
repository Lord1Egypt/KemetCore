# cocotb + Verilator testbenches for the BastCore tensor core.
#   make CORE=mac    (default)   -> bast_mac single PE (+ hapi_bf16_mul, hapi_fp32_add)
#   make CORE=grid               -> bast_mac_grid RxC systolic array (+ bast_mac, hapi)
#   make CORE=int8               -> bast_int8_mac INT8 MAC cell (pure integer)
#   make CORE=fp16              -> bast_fp16_mac (fp16 mul / fp32 acc) + hapi fp16
#   make CORE=int8grid           -> bast_int8_grid RxC INT8 systolic array (+ int8_mac)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= mac

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# bast_mac instantiates the verified HapiCore primitives, so they are compiled in.
ifeq ($(CORE),fp16grid)
  VERILOG_SOURCES = $(PWD)/../bast_fp16_grid.sv $(PWD)/../bast_fp16_mac.sv $(HAPI)/hapi_fp16_mul.sv $(HAPI)/hapi_fp16_to_fp32.sv $(HAPI)/hapi_fp32_add.sv
  TOPLEVEL = bast_fp16_grid
  MODULE   = test_fp16_grid
else ifeq ($(CORE),fp16)
  VERILOG_SOURCES = $(PWD)/../bast_fp16_mac.sv $(HAPI)/hapi_fp16_mul.sv $(HAPI)/hapi_fp16_to_fp32.sv $(HAPI)/hapi_fp32_add.sv
  TOPLEVEL = bast_fp16_mac
  MODULE   = test_fp16
else ifeq ($(CORE),int8grid)
  VERILOG_SOURCES = $(PWD)/../bast_int8_grid.sv $(PWD)/../bast_int8_mac.sv
  TOPLEVEL = bast_int8_grid
  MODULE   = test_int8_grid
else ifeq ($(CORE),int8)
  VERILOG_SOURCES = $(PWD)/../bast_int8_mac.sv
  TOPLEVEL = bast_int8_mac
  MODULE   = test_int8_mac
else ifeq ($(CORE),grid)
  VERILOG_SOURCES = $(PWD)/../bast_mac_grid.sv $(PWD)/../bast_mac.sv \
                    $(HAPI)/hapi_bf16_mul.sv $(HAPI)/hapi_fp32_add.sv
  TOPLEVEL = bast_mac_grid
  MODULE   = test_mac_grid
else
  VERILOG_SOURCES = $(PWD)/../bast_mac.sv $(HAPI)/hapi_bf16_mul.sv $(HAPI)/hapi_fp32_add.sv
  TOPLEVEL = bast_mac
  MODULE   = test_mac
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
