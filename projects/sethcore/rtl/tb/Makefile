# cocotb + Verilator testbenches for SethCore.
#   make CORE=alu      (default) -> seth_alu
#   make CORE=muldiv             -> seth_muldiv
#   make CORE=imm                -> seth_imm
#   make CORE=regfile            -> seth_regfile
#   make CORE=aluctl             -> seth_aluctl
#   make CORE=decode             -> seth_decode
#   make CORE=csr                -> seth_csr (Zicsr CSR datapath unit)
#   make CORE=csru               -> seth_csru (Zicsr CSR register bank + seth_csr)
#   make CORE=mcsr               -> seth_mcsr (M-mode CSR file: mstatus/mtvec/mepc/... WARL)
#   make CORE=trap               -> seth_trap (M-mode trap vectoring + mepc/mcause/mstatus)
#   make CORE=corecsr            -> seth_core_csr (integrated single-cycle RV32IMZicsr core)
#   make CORE=branch             -> seth_branch (branch-condition unit)
#   make CORE=lsu                -> seth_lsu (load/store format unit)
#   make CORE=core               -> seth_core (integrated single-cycle RV32IM)
#   make CORE=pipeline           -> seth_pipeline (5-stage interlocked RV32IM)
#   make CORE=fwd                -> seth_pipeline_fwd vs seth_pipeline (forwarding)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= alu
PWD := $(shell pwd)

ifeq ($(CORE),corecsr)
  VERILOG_SOURCES = $(PWD)/../seth_core_csr.sv $(PWD)/../seth_decode.sv $(PWD)/../seth_imm.sv \
                    $(PWD)/../seth_aluctl.sv $(PWD)/../seth_alu.sv $(PWD)/../seth_muldiv.sv \
                    $(PWD)/../seth_regfile.sv $(PWD)/../seth_trap.sv
  TOPLEVEL = seth_core_csr
  MODULE   = test_core_csr
else ifeq ($(CORE),trap)
  VERILOG_SOURCES = $(PWD)/../seth_trap.sv
  TOPLEVEL = seth_trap
  MODULE   = test_trap
else ifeq ($(CORE),mcsr)
  VERILOG_SOURCES = $(PWD)/../seth_mcsr.sv
  TOPLEVEL = seth_mcsr
  MODULE   = test_mcsr
else ifeq ($(CORE),lsu)
  VERILOG_SOURCES = $(PWD)/../seth_lsu.sv
  TOPLEVEL = seth_lsu
  MODULE   = test_lsu
else ifeq ($(CORE),branch)
  VERILOG_SOURCES = $(PWD)/../seth_branch.sv
  TOPLEVEL = seth_branch
  MODULE   = test_branch
else ifeq ($(CORE),csru)
  VERILOG_SOURCES = $(PWD)/../seth_csru.sv $(PWD)/../seth_csr.sv
  TOPLEVEL = seth_csru
  MODULE   = test_csru
else ifeq ($(CORE),csr)
  VERILOG_SOURCES = $(PWD)/../seth_csr.sv
  TOPLEVEL = seth_csr
  MODULE   = test_csr
else ifeq ($(CORE),muldiv)
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
else ifeq ($(CORE),core)
  VERILOG_SOURCES = $(PWD)/../seth_decode.sv $(PWD)/../seth_imm.sv \
                    $(PWD)/../seth_aluctl.sv $(PWD)/../seth_alu.sv \
                    $(PWD)/../seth_muldiv.sv $(PWD)/../seth_regfile.sv \
                    $(PWD)/../seth_core.sv
  TOPLEVEL = seth_core
  MODULE   = test_core
else ifeq ($(CORE),pipeline)
  VERILOG_SOURCES = $(PWD)/../seth_decode.sv $(PWD)/../seth_imm.sv \
                    $(PWD)/../seth_aluctl.sv $(PWD)/../seth_alu.sv \
                    $(PWD)/../seth_muldiv.sv $(PWD)/../seth_regfile.sv \
                    $(PWD)/../seth_pipeline.sv
  TOPLEVEL = seth_pipeline
  MODULE   = test_pipeline
else ifeq ($(CORE),fwd)
  VERILOG_SOURCES = $(PWD)/../seth_decode.sv $(PWD)/../seth_imm.sv \
                    $(PWD)/../seth_aluctl.sv $(PWD)/../seth_alu.sv \
                    $(PWD)/../seth_muldiv.sv $(PWD)/../seth_regfile.sv \
                    $(PWD)/../seth_pipeline.sv $(PWD)/../seth_pipeline_fwd.sv \
                    $(PWD)/../seth_pipeline_cmp.sv
  TOPLEVEL = seth_pipeline_cmp
  MODULE   = test_pipeline_fwd
else
  VERILOG_SOURCES = $(PWD)/../seth_alu.sv
  TOPLEVEL = seth_alu
  MODULE   = test_alu
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
# If cocotb and Verilator use different Pythons, run via ./run_sim.sh
include $(shell cocotb-config --makefiles)/Makefile.sim
