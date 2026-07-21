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

# Yosys 0.33 uses 'const rand reg', Yosys 0.65 requires 'rand const reg',
# but '(* anyconst *) reg' is the standard attribute that works on both!
sed -i 's/const rand reg/(* anyconst *) reg/g' ../../checks/rvfi_macros.vh

python3 ../../checks/genchecks.py
make -C checks -j$(nproc) || true

# sby does NOT propagate FAIL as a nonzero process exit code (confirmed: a
# failing check prints "DONE (FAIL, rc=0)" and make happily reports success)
# so exit status here has to come from reading each check's status file.
fails=""
for f in checks/*/status; do
    grep -q "^PASS" "$f" || fails="$fails $(dirname "$f" | xargs basename)"
done
if [ -n "$fails" ]; then
    echo "SethCore riscv-formal proofs FAILED ❌ :$fails"
    exit 1
fi
echo "SethCore riscv-formal proofs PROVED ✅"
