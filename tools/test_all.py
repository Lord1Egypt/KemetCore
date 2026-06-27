#!/usr/bin/env python3
"""Run every project's Phase 0/1 test suite and report a per-project summary.

Pure pytest under the hood; exits non-zero if anything fails (CI gate).
Usage: python tools/test_all.py
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rc = subprocess.call([sys.executable, "-m", "pytest", "projects/", "-q"], cwd=ROOT)
    print("\n" + ("ALL GREEN ✅" if rc == 0 else "FAILURES ❌"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
