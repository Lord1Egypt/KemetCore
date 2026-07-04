# cocotb + Verilator testbenches for SobekCore.
#   make CORE=dot3  (default)  -> sobek_dot3 fp32 3-element dot product (+ hapi fp32)
#   make CORE=cross            -> sobek_cross fp32 3-D cross product (+ hapi fp32)
#   make CORE=scale            -> sobek_scale fp32 scalar-vector product (+ hapi fp32)
#   make CORE=recip            -> sobek_recip fp32 reciprocal 1/x (+ hapi fp32 div)
#   make CORE=normalize        -> sobek_normalize fp32 v/||v|| (+ dot3 + hapi sqrt/div/mul)
#   make CORE=reflect          -> sobek_reflect fp32 d-2(d.n)n (+ dot3 + hapi mul/add)
#   make CORE=raypoint         -> sobek_ray_point fp32 o+t*d (+ hapi mul/add)
#   make CORE=lerp             -> sobek_lerp fp32 a+t*(b-a) (+ hapi mul/add)
#   make CORE=length           -> sobek_length fp32 ||v|| (+ dot3 + hapi sqrt)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= dot3

PWD := $(shell pwd)
HAPI := $(PWD)/../../../hapicore/rtl

# The Sobek primitives instantiate the verified HapiCore fp32 blocks, so they compile in.
ifeq ($(CORE),cross)
VERILOG_SOURCES = $(PWD)/../sobek_cross.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_cross
MODULE   = test_cross
else ifeq ($(CORE),scale)
VERILOG_SOURCES = $(PWD)/../sobek_scale.sv $(HAPI)/hapi_fp32_mul.sv
TOPLEVEL = sobek_scale
MODULE   = test_scale
else ifeq ($(CORE),recip)
VERILOG_SOURCES = $(PWD)/../sobek_recip.sv $(HAPI)/hapi_fp32_div.sv
TOPLEVEL = sobek_recip
MODULE   = test_recip
else ifeq ($(CORE),normalize)
VERILOG_SOURCES = $(PWD)/../sobek_normalize.sv $(PWD)/../sobek_dot3.sv \
                  $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv \
                  $(HAPI)/hapi_fp32_sqrt.sv $(HAPI)/hapi_fp32_div.sv
TOPLEVEL = sobek_normalize
MODULE   = test_normalize
else ifeq ($(CORE),reflect)
VERILOG_SOURCES = $(PWD)/../sobek_reflect.sv $(PWD)/../sobek_dot3.sv \
                  $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_reflect
MODULE   = test_reflect
else ifeq ($(CORE),raypoint)
VERILOG_SOURCES = $(PWD)/../sobek_ray_point.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_ray_point
MODULE   = test_raypoint
else ifeq ($(CORE),lerp)
VERILOG_SOURCES = $(PWD)/../sobek_lerp.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_lerp
MODULE   = test_lerp
else ifeq ($(CORE),length)
VERILOG_SOURCES = $(PWD)/../sobek_length.sv $(PWD)/../sobek_dot3.sv \
                  $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv $(HAPI)/hapi_fp32_sqrt.sv
TOPLEVEL = sobek_length
MODULE   = test_length
else ifeq ($(CORE),dot3)
VERILOG_SOURCES = $(PWD)/../sobek_dot3.sv $(HAPI)/hapi_fp32_mul.sv $(HAPI)/hapi_fp32_add.sv
TOPLEVEL = sobek_dot3
MODULE   = test_dot3
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
