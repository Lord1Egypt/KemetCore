# cocotb + Verilator testbenches for AtumCore (RVV).
#   make CORE=valu   (default)   -> atum_valu (vector integer ALU lane array)
#   make CORE=vfpu               -> atum_vfpu (fp32 vector lane: vfadd/vfmul)
#   make CORE=vredu              -> atum_vredu (vredsum/vredmax reduction)
#   make CORE=vexec              -> atum_vexec (integrated vector execute unit)
#   make CORE=vregfile           -> atum_vregfile (vector register file)
#   make CORE=vsetvl             -> atum_vsetvl (VL = min(avl, VLMAX))
#   make CORE=vcore              -> atum_vcore (single-cycle vector core)
#   make CORE=vmask              -> atum_vmask (compare-to-mask: vmseq/vmslt/...)
#   make CORE=vmlogic            -> atum_vmlogic (mask logic: vmand/vmor/vmxor/...)
#   make CORE=vmpopc             -> atum_vmpopc (mask reduce: vcpop/vfirst)
#   make CORE=viota              -> atum_viota (mask->index: viota/vid)
#   make CORE=vcompress          -> atum_vcompress (stream compaction / filter)
#   make CORE=vrgather           -> atum_vrgather (register gather / permute)
#   make CORE=vslide             -> atum_vslide (slideup / slidedown)
#   make CORE=vmerge             -> atum_vmerge (mask-driven element select)
#   make CORE=vfsgnj             -> atum_vfsgnj (fp sign inject: copysign/neg/abs)
#   make CORE=vfminmax           -> atum_vfminmax (fp32 vfmin / vfmax)
#   make CORE=vfclass            -> atum_vfclass (fp32 classify -> 10-bit class)
#   make CORE=vmsbf              -> atum_vmsbf (mask set before/incl/only first)
#   make CORE=vmv                -> atum_vmv (vmv.v.x splat / vmv.v.v copy)
#   make CORE=vslide1            -> atum_vslide1 (vslide1up / vslide1down)
#   make CORE=vfcvt              -> atum_vfcvt (int<->fp32 convert: vfcvt.*)
#   make CORE=vfsub              -> atum_vfsub (fp32 vfsub / vfrsub)
#   make CORE=vmfcmp             -> atum_vmfcmp (fp32 compare->mask: vmfeq/vmflt/...)
#   make CORE=vfmacc             -> atum_vfmacc (fp32 fused MAC: vfmacc / vfmsac)
#   make CORE=vsadd              -> atum_vsadd (saturating int add/sub: vsaddu/vsadd/...)
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
else ifeq ($(CORE),vmask)
  VERILOG_SOURCES = $(PWD)/../atum_vmask.sv
  TOPLEVEL = atum_vmask
  MODULE   = test_vmask
else ifeq ($(CORE),vmlogic)
  VERILOG_SOURCES = $(PWD)/../atum_vmlogic.sv
  TOPLEVEL = atum_vmlogic
  MODULE   = test_vmlogic
else ifeq ($(CORE),vmpopc)
  VERILOG_SOURCES = $(PWD)/../atum_vmpopc.sv
  TOPLEVEL = atum_vmpopc
  MODULE   = test_vmpopc
else ifeq ($(CORE),viota)
  VERILOG_SOURCES = $(PWD)/../atum_viota.sv
  TOPLEVEL = atum_viota
  MODULE   = test_viota
else ifeq ($(CORE),vcompress)
  VERILOG_SOURCES = $(PWD)/../atum_vcompress.sv
  TOPLEVEL = atum_vcompress
  MODULE   = test_vcompress
else ifeq ($(CORE),vrgather)
  VERILOG_SOURCES = $(PWD)/../atum_vrgather.sv
  TOPLEVEL = atum_vrgather
  MODULE   = test_vrgather
else ifeq ($(CORE),vslide)
  VERILOG_SOURCES = $(PWD)/../atum_vslide.sv
  TOPLEVEL = atum_vslide
  MODULE   = test_vslide
else ifeq ($(CORE),vmerge)
  VERILOG_SOURCES = $(PWD)/../atum_vmerge.sv
  TOPLEVEL = atum_vmerge
  MODULE   = test_vmerge
else ifeq ($(CORE),vfsgnj)
  VERILOG_SOURCES = $(PWD)/../atum_vfsgnj.sv
  TOPLEVEL = atum_vfsgnj
  MODULE   = test_vfsgnj
else ifeq ($(CORE),vfminmax)
  VERILOG_SOURCES = $(PWD)/../atum_vfminmax.sv
  TOPLEVEL = atum_vfminmax
  MODULE   = test_vfminmax
else ifeq ($(CORE),vfclass)
  VERILOG_SOURCES = $(PWD)/../atum_vfclass.sv
  TOPLEVEL = atum_vfclass
  MODULE   = test_vfclass
else ifeq ($(CORE),vmsbf)
  VERILOG_SOURCES = $(PWD)/../atum_vmsbf.sv
  TOPLEVEL = atum_vmsbf
  MODULE   = test_vmsbf
else ifeq ($(CORE),vmv)
  VERILOG_SOURCES = $(PWD)/../atum_vmv.sv
  TOPLEVEL = atum_vmv
  MODULE   = test_vmv
else ifeq ($(CORE),vslide1)
  VERILOG_SOURCES = $(PWD)/../atum_vslide1.sv
  TOPLEVEL = atum_vslide1
  MODULE   = test_vslide1
else ifeq ($(CORE),vfcvt)
  VERILOG_SOURCES = $(PWD)/../atum_vfcvt.sv
  TOPLEVEL = atum_vfcvt
  MODULE   = test_vfcvt
else ifeq ($(CORE),vsadd)
  VERILOG_SOURCES = $(PWD)/../atum_vsadd.sv
  TOPLEVEL = atum_vsadd
  MODULE   = test_vsadd
else ifeq ($(CORE),vfsub)
  VERILOG_SOURCES = $(HAPI)/hapi_fp32_add.sv $(PWD)/../atum_vfsub.sv
  TOPLEVEL = atum_vfsub
  MODULE   = test_vfsub
else ifeq ($(CORE),vmfcmp)
  VERILOG_SOURCES = $(PWD)/../atum_vmfcmp.sv
  TOPLEVEL = atum_vmfcmp
  MODULE   = test_vmfcmp
else ifeq ($(CORE),vfmacc)
  VERILOG_SOURCES = $(HAPI)/hapi_fp32_fma.sv $(PWD)/../atum_vfmacc.sv
  TOPLEVEL = atum_vfmacc
  MODULE   = test_vfmacc
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
