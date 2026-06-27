# cocotb + Verilator testbench for AnubisCore sha256_core
TOPLEVEL_LANG = verilog
SIM ?= verilator

PWD := $(shell pwd)
VERILOG_SOURCES = $(PWD)/../sha256_core.sv

TOPLEVEL = sha256_core
MODULE   = test_sha256

# Verilator: synchronous design, no timing constructs needed
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters (e.g. a
# conda cocotb + the system /usr/bin/python3 that Verilator hardcodes), run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
