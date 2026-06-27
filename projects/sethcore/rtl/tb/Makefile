# cocotb + Verilator testbenches for SethCore.
#   make CORE=alu      (default) -> seth_alu
#   make CORE=muldiv             -> seth_muldiv
#   make CORE=imm                -> seth_imm
#   make CORE=regfile            -> seth_regfile
#   make CORE=aluctl             -> seth_aluctl
#   make CORE=decode             -> seth_decode
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= alu
PWD := $(shell pwd)

ifeq ($(CORE),muldiv)
  VERILOG_SOURCES = $(PWD)/../seth_muldiv.sv
  TOPLEVEL = seth_muldiv
  MODULE   = test_muldiv
else ifeq ($(CORE),imm)
  VERILOG_SOURCES = $(PWD)/../seth_imm.sv
  TOPLEVEL = seth_imm
  MODULE   = test_imm
else ifeq ($(CORE),regfile)
  VERILOG_SOURCES = $(PWD)/../seth_regfile.sv
  TOPLEVEL = seth_regfile
  MODULE   = test_regfile
else ifeq ($(CORE),aluctl)
  VERILOG_SOURCES = $(PWD)/../seth_aluctl.sv
  TOPLEVEL = seth_aluctl
  MODULE   = test_aluctl
else ifeq ($(CORE),decode)
  VERILOG_SOURCES = $(PWD)/../seth_decode.sv
  TOPLEVEL = seth_decode
  MODULE   = test_decode
else
  VERILOG_SOURCES = $(PWD)/../seth_alu.sv
  TOPLEVEL = seth_alu
  MODULE   = test_alu
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
# If cocotb and Verilator use different Pythons, run via ./run_sim.sh
include $(shell cocotb-config --makefiles)/Makefile.sim
