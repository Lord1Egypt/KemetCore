# cocotb + Verilator testbenches for RaCore.
#   make CORE=kai  (default)  -> ra_kai_regs (KAI MMIO register block)
#   make CORE=noc             -> ra_noc_arbiter (round-robin NoC arbiter)
#   make CORE=dma             -> ra_dma (descriptor DMA engine, 1D + 2D)
#   make CORE=kaidma          -> ra_kai_dma (KAI-wrapped DMA accelerator)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= kai
PWD := $(shell pwd)

ifeq ($(CORE),kaidma)
  VERILOG_SOURCES = $(PWD)/../ra_kai_dma.sv $(PWD)/../ra_kai_regs.sv $(PWD)/../ra_dma.sv
  TOPLEVEL = ra_kai_dma
  MODULE   = test_kai_dma
else ifeq ($(CORE),dma)
  VERILOG_SOURCES = $(PWD)/../ra_dma.sv
  TOPLEVEL = ra_dma
  MODULE   = test_dma
else ifeq ($(CORE),noc)
  VERILOG_SOURCES = $(PWD)/../ra_noc_arbiter.sv
  TOPLEVEL = ra_noc_arbiter
  MODULE   = test_noc
else
VERILOG_SOURCES = $(PWD)/../ra_kai_regs.sv
TOPLEVEL = ra_kai_regs
MODULE   = test_kai_regs
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing
include $(shell cocotb-config --makefiles)/Makefile.sim
