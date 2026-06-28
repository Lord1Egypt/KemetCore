# cocotb + Verilator testbenches for AtumCore (RVV).
#   make CORE=valu   (default)   -> atum_valu (vector integer ALU lane array)
#   make CORE=vfpu               -> atum_vfpu (fp32 vector lane: vfadd/vfmul)
#   make CORE=vredu              -> atum_vredu (vredsum/vredmax reduction)
#   make CORE=vexec              -> atum_vexec (integrated vector execute unit)
#   make CORE=vregfile           -> atum_vregfile (vector register file)
#   make CORE=vsetvl             -> atum_vsetvl (VL = min(avl, VLMAX))
#   make CORE=vcore              -> atum_vcore (single-cycle vector core)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= valu

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

ifeq ($(CORE),vcore)
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv $(PWD)/../atum_vfpu.sv \
                    $(PWD)/../atum_vredu.sv $(HAPI)/hapi_fp32_mul.sv \
                    $(HAPI)/hapi_fp32_add.sv $(PWD)/../atum_vexec.sv \
                    $(PWD)/../atum_vregfile.sv $(PWD)/../atum_vsetvl.sv \
                    $(PWD)/../atum_vcore.sv
  TOPLEVEL = atum_vcore
  MODULE   = test_vcore
else ifeq ($(CORE),vregfile)
  VERILOG_SOURCES = $(PWD)/../atum_vregfile.sv
  TOPLEVEL = atum_vregfile
  MODULE   = test_vregfile
else ifeq ($(CORE),vsetvl)
  VERILOG_SOURCES = $(PWD)/../atum_vsetvl.sv
  TOPLEVEL = atum_vsetvl
  MODULE   = test_vsetvl
else ifeq ($(CORE),vexec)
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv $(PWD)/../atum_vfpu.sv \
                    $(PWD)/../atum_vredu.sv $(HAPI)/hapi_fp32_mul.sv \
                    $(HAPI)/hapi_fp32_add.sv $(PWD)/../atum_vexec.sv
  TOPLEVEL = atum_vexec
  MODULE   = test_vexec
else ifeq ($(CORE),vredu)
  VERILOG_SOURCES = $(PWD)/../atum_vredu.sv
  TOPLEVEL = atum_vredu
  MODULE   = test_vredu
else ifeq ($(CORE),vfpu)
  VERILOG_SOURCES = $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv \
                    $(PWD)/../atum_vfpu.sv
  TOPLEVEL = atum_vfpu
  MODULE   = test_vfpu
else ifeq ($(CORE),valu)
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv
  TOPLEVEL = atum_valu
  MODULE   = test_valu
else
  VERILOG_SOURCES = $(PWD)/../atum_valu.sv
  TOPLEVEL = atum_valu
  MODULE   = test_valu
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# If cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
