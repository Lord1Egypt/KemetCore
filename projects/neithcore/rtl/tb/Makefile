# cocotb + Verilator testbenches for NeithCore NTT.
#   make CORE=modmul    (default)   -> neith_modmul
#   make CORE=butterfly             -> neith_butterfly (+ neith_modmul)
#   make CORE=ntt                   -> neith_ntt 256-pt engine (+ butterfly + modmul)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= modmul

PWD := $(shell pwd)

ifeq ($(CORE),butterfly)
  VERILOG_SOURCES = $(PWD)/../neith_butterfly.sv $(PWD)/../neith_modmul.sv
  TOPLEVEL = neith_butterfly
  MODULE   = test_butterfly
else ifeq ($(CORE),ntt)
  VERILOG_SOURCES = $(PWD)/../neith_ntt.sv $(PWD)/../neith_butterfly.sv $(PWD)/../neith_modmul.sv
  TOPLEVEL = neith_ntt
  MODULE   = test_ntt
else
  VERILOG_SOURCES = $(PWD)/../neith_modmul.sv
  TOPLEVEL = neith_modmul
  MODULE   = test_modmul
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
