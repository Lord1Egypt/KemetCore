# cocotb + Verilator testbenches for the BastCore tensor core.
#   make CORE=mac    (default)   -> bast_mac single PE (+ hapi_bf16_mul, hapi_fp32_add)
#   make CORE=grid               -> bast_mac_grid RxC systolic array (+ bast_mac, hapi)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= mac

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# bast_mac instantiates the verified HapiCore primitives, so they are compiled in.
ifeq ($(CORE),grid)
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
