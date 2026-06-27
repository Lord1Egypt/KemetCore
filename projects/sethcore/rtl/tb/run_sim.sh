#!/usr/bin/env bash
# Run the seth_alu cocotb testbench with a consistent Python (see anubiscore note).
set -euo pipefail
cd "$(dirname "$0")"
PYBIN="$(cocotb-config --python-bin)"
make clean >/dev/null 2>&1 || true
exec make PYTHON3="$PYBIN" "$@"
