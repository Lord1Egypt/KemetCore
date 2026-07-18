#!/usr/bin/env bash
# Run riscv-formal checks for SethCore.
set -euo pipefail
# genchecks.py hardcodes ../../insns, so it must run inside the riscv-formal tree
YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
SBY="${SBY:-$(command -v sby || echo $HOME/.local/bin/sby)}"

export PATH="$(dirname "$SBY"):$(dirname "$YOSYS"):$PATH"

ROOT_DIR="$(cd "$(dirname "$0")/../../../" && pwd)"
cd "$ROOT_DIR"
rm -rf third_party/riscv-formal/cores/sethcore
cp -r projects/sethcore/formal/riscv_formal_config third_party/riscv-formal/cores/sethcore
cd third_party/riscv-formal/cores/sethcore

# Patch genchecks.py to use -formal so Yosys parses `rand reg` correctly
sed -i 's/read_verilog -sv/read_verilog -sv -formal/g' ../../checks/genchecks.py
sed -i 's/read_verilog -sv/read_verilog -sv -formal/g' checks.cfg

python3 ../../checks/genchecks.py
make -C checks -j$(nproc)
echo "SethCore riscv-formal proofs PROVED ✅"
