# WORKLOG

## 2026-07-15
- **Branch**: feat/gebcore-formal-prune
- **Action**: Implemented full formal proof for geb_prune 2:4 structured-sparsity invariant (exactly 2 kept, and output values match inputs). Added embedded asserts to `projects/gebcore/rtl/geb_prune.sv` under `ifdef FORMAL`. Mutation-tested by temporarily changing the kept limit to 3, which successfully failed.
- **Tests**:
  - `projects/gebcore/formal/run_formal.sh` -> `formal_prune PROVED ✅`
  - `projects/gebcore/rtl/tb/run_sim.sh CORE=prune` -> `test_prune passed (1/1)`
  - `projects/gebcore/synth/run_synth.sh` -> `0 latches asserted`
- **Commit**: 3f564bf
- **PR**: #174
