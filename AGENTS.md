# KemetCore Agent Playbook & Memory

This file serves as the persistent memory and operational playbook for agentic AI assistants working on KemetCore. Read this file immediately when asked to "continue KemetCore".

## 1. Project Navigation & State
- **Golden Models**: `projects/<core>/golden/`
- **RTL**: `projects/<core>/rtl/`
- **Testbenches (cocotb)**: `projects/<core>/rtl/tb/`
- **Formal Proofs**: `projects/<core>/formal/`
- **Progress Tracking**: Progress is tracked centrally in `tools/manifest.py`. After any task completion, update `manifest.py` and run `python tools/gen_tracking.py` to regenerate `PROGRESS.md` and the individual `STEPS.md` files.

## 2. The Verification Loop (The 3 Gates)
Before any task is considered "complete", it must pass three gates:
1. **Bit-exact Simulation**: Run `./run_sim.sh CORE=<module>` in the `tb/` directory. Must match golden model exactly.
2. **0-Latch Synthesis**: Run `./run_synth.sh` in the `synth/` directory. Check the `reports/` to guarantee exactly 0 latches are asserted.
3. **Formal Verification**: Run `./run_formal.sh` in the `formal/` directory (where applicable). 
   - **Crucial Yosys 0.65 constraint**: Yosys 0.65 does not support `bind` or cross-module hierarchical references. Embed `assert`, `assume`, and `cover` statements directly inside the RTL under `` `ifdef FORMAL ``.
   - **Mutation Testing**: All formal proofs MUST be mutation-tested. Temporarily break the RTL constraint to ensure the proof actively catches the failure (`FAILED ❌`), then restore the RTL and ensure it passes.

## 3. Standard Operating Procedure (SOP)
1. **Resume**: Check `docs/agent/RESUME.md` to see the current state and next immediate step.
2. **Branch**: Always branch off `main` (e.g. `git checkout -b feat/<core>-<task>`).
3. **Scope**: Do exactly ONE small task from `TASK_MENU.md` or `RESUME.md`. Build the smallest correct thing.
4. **Log**: After completing the task and passing all verification gates, record your actions, test commands + results, commit hash, and PR number in `docs/agent/WORKLOG.md`.
5. **Halt**: Push your branch, open a PR via `gh pr create`, update `docs/agent/RESUME.md` with the new state, and **STOP**. 
6. **No Self-Merges**: Wait for the user (Mohamed) to explicitly review and say "merge" before attempting to merge any PR.

## 4. Current State
- Refer to `docs/agent/RESUME.md` for the exact current task status.
- Refer to `PROGRESS.md` for the overarching project completion matrix.
