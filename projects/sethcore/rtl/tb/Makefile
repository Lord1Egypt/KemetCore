# cocotb + Verilator testbench for SethCore seth_alu
TOPLEVEL_LANG = verilog
SIM ?= verilator
PWD := $(shell pwd)
VERILOG_SOURCES = $(PWD)/../seth_alu.sv
TOPLEVEL = seth_alu
MODULE   = test_alu
EXTRA_ARGS += --no-timing
# If cocotb and Verilator use different Pythons, run via ./run_sim.sh
include $(shell cocotb-config --makefiles)/Makefile.sim
