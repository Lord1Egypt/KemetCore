#!/usr/bin/env bash
# Run the cocotb SHA-256 testbench, forcing Verilator's build-time Python to match
# the interpreter cocotb embeds. On a single-Python machine this is a harmless no-op.
set -euo pipefail
cd "$(dirname "$0")"
PYBIN="$(cocotb-config --python-bin)"
make clean >/dev/null 2>&1 || true
exec make PYTHON3="$PYBIN" "$@"
