#!/usr/bin/env bash
# Run riscv-formal checks for SethCore.
set -euo pipefail
cd "$(dirname "$0")/riscv_formal_config"

YOSYS="${YOSYS:-$(command -v yosys || echo $HOME/miniconda3/envs/eda/bin/yosys)}"
SMTBMC="${SMTBMC:-$(command -v yosys-smtbmc || echo $HOME/miniconda3/envs/eda/bin/yosys-smtbmc)}"
SBY="${SBY:-$(command -v sby || echo $HOME/.local/bin/sby)}"

export PATH="$(dirname "$SBY"):$(dirname "$YOSYS"):$PATH"

python3 ../../../../third_party/riscv-formal/checks/genchecks.py
make -C checks -j$(nproc)
echo "SethCore riscv-formal proofs PROVED ✅"
