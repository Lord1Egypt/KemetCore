#!/usr/bin/env bash
# Run a SobekCore cocotb testbench, forcing Verilator's build-time Python to match
# the interpreter cocotb embeds.
set -euo pipefail
cd "$(dirname "$0")"
PYBIN="$(cocotb-config --python-bin)"
make clean >/dev/null 2>&1 || true
exec make PYTHON3="$PYBIN" "$@"
