# REVIEW CHECKLIST — Run This Before You Call Anything Done

Go through every line. If you cannot tick a box with evidence from THIS session,
the task is not done. This is also the checklist Mohamed (and his reviewer) will
run against your work — pass it yourself first.

## Correctness
- [ ] I read the golden model and the neighbouring RTL before writing.
- [ ] cocotb testbench passes **bit-exact** vs golden — I ran it and read the output.
      Command + result is in the worklog.
- [ ] `run_synth.sh` reports **0 latches**. I ran it and read the output.
- [ ] If a formal proof: it is **non-vacuous** (`grep -c assert build/*.smt2` > 0),
      **mutation-tested** (corrupt ⇒ FAIL, real ⇒ PASS), and **honestly labeled**.
- [ ] If P&R: WNS ≥ 0 (timing closes) and route DRC = 0. I did not commit a
      non-closing design.
- [ ] `pytest projects/ -q` still green (I didn't break another core).

## Honesty
- [ ] The tracker reflects reality: `partial` where partial, `done` only where
      genuinely complete. I ran `python tools/gen_tracking.py`.
- [ ] My commit message and PR body state what was verified and how — no
      overclaiming, no "should work".
- [ ] Any gap / deferral / known-limitation is written down, not hidden.

## Hygiene
- [ ] No stubs, no `TODO: later`, no dead code, no unrelated refactors.
- [ ] No new dependencies. Standard library + existing toolchain only.
- [ ] No secrets, tokens, or keys in code, config, logs, or test fixtures.
- [ ] Style matches the surrounding code (naming, reset convention, comment density).
- [ ] I did not hand-edit a generated file (`PROGRESS.md`, `*/CHECKPOINTS.md`, etc.).

## Process
- [ ] Work is committed AND pushed (nothing left dirty).
- [ ] `docs/agent/WORKLOG.md` has an entry for this step with the test result,
      commit hash, and PR number.
- [ ] The PR is open and both required CI checks ("Phase 0/1 tests", "Phase 2 RTL")
      are green.
- [ ] I did NOT merge — I stopped and am waiting for Mohamed's explicit "merge".

## Self-rating (write this into the worklog for Mohamed)
In one line: what you shipped, the strongest evidence it's correct, and the single
weakest / least-certain part of it. Honesty about the weak part is what earns trust.
