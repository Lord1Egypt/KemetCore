# cocotb + Verilator testbenches for AnubisCore.
#   make CORE=sha256   (default)   -> sha256_core
#   make CORE=sha3                 -> sha3_256_core
#   make CORE=sha512               -> sha512_core
#   make CORE=sha3_512             -> sha3_512_core
#   make CORE=sha3_384             -> sha3_384_core
#   make CORE=sha3_224             -> sha3_224_core
#   make CORE=hmac                 -> hmac_sha256_core (+ sha256_core)
#   make CORE=hmac512              -> hmac_sha512_core (+ sha512_core)
#   make CORE=shake128            -> shake128_xof_core (XOF: absorb + squeeze)
TOPLEVEL_LANG = verilog
SIM ?= verilator
CORE ?= sha256

PWD := $(shell pwd)

ifeq ($(CORE),shake128)
  VERILOG_SOURCES = $(PWD)/../shake128_xof_core.sv
  TOPLEVEL = shake128_xof_core
  MODULE   = test_shake128
else ifeq ($(CORE),hmac512)
  VERILOG_SOURCES = $(PWD)/../hmac_sha512_core.sv $(PWD)/../sha512_core.sv
  TOPLEVEL = hmac_sha512_core
  MODULE   = test_hmac_sha512
else ifeq ($(CORE),hmac)
  VERILOG_SOURCES = $(PWD)/../hmac_sha256_core.sv $(PWD)/../sha256_core.sv
  TOPLEVEL = hmac_sha256_core
  MODULE   = test_hmac_sha256
else ifeq ($(CORE),sha3_224)
  VERILOG_SOURCES = $(PWD)/../sha3_224_core.sv
  TOPLEVEL = sha3_224_core
  MODULE   = test_sha3_224
else ifeq ($(CORE),sha3_384)
  VERILOG_SOURCES = $(PWD)/../sha3_384_core.sv
  TOPLEVEL = sha3_384_core
  MODULE   = test_sha3_384
else ifeq ($(CORE),sha3_512)
  VERILOG_SOURCES = $(PWD)/../sha3_512_core.sv
  TOPLEVEL = sha3_512_core
  MODULE   = test_sha3_512
else ifeq ($(CORE),sha512)
  VERILOG_SOURCES = $(PWD)/../sha512_core.sv
  TOPLEVEL = sha512_core
  MODULE   = test_sha512
else ifeq ($(CORE),sha3)
  VERILOG_SOURCES = $(PWD)/../sha3_256_core.sv
  TOPLEVEL = sha3_256_core
  MODULE   = test_sha3
else
  VERILOG_SOURCES = $(PWD)/../sha256_core.sv
  TOPLEVEL = sha256_core
  MODULE   = test_sha256
endif

SIM_BUILD = sim_build_$(CORE)
EXTRA_ARGS += --no-timing

# NOTE: if cocotb and Verilator resolve to different Python interpreters, run via
# ./run_sim.sh, which passes PYTHON3=$(cocotb-config --python-bin) to make.
include $(shell cocotb-config --makefiles)/Makefile.sim
