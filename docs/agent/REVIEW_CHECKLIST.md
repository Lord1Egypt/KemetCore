# 🔁 SELF-AUDIT PROTOCOL (permanent — run before EVERY PR, all future phases)

Mohamed asked for this to be standing procedure. Then run it, top to bottom, before opening every PR. Every item is a
mistake that actually happened in this repo — none are theoretical.

## A. Diff hygiene (catches: duplicated reset line, dead `load_use`, root junk)
- [ ] Read your ENTIRE diff line-by-line before opening the PR (`git diff main...HEAD`).
      You are looking for: duplicated lines, dead/unused signals or wires,
      leftover debug prints/`$display`, stray comments or whitespace-only edits.
- [ ] `git status` is CLEAN after your final commit — no modified-but-uncommitted
      files (the .stat incident), no scratch files anywhere in the repo
      (use `/tmp` or a gitignored dir for scratch, never the repo root).

## B. Logic-rewrite guard audit (catches: the unguarded stall rewrite)
- [ ] If you rewrote or inlined ANY condition, diff the old and new boolean
      expressions term-by-term. Every validity qualifier (`id_valid`,
      `ex_valid`, `busy`, `state==...`) in the old expression must be present
      or provably redundant in the new one. Write one sentence in the PR body:
      "old condition X, new condition Y, dropped terms Z because …".
- [ ] Think about bubbles/flush: what value do the stage registers hold when
      `*_valid` is 0? Any signal you read without a `*_valid` guard is stale.

## C. Verification honesty (catches: "PASS" claims CI never checked)
- [ ] Re-run the full sim + synth commands AFTER your final commit (not before
      your last edit) and paste the raw outputs into the PR body.
- [ ] Every new RTL module gets its cocotb test added to CI **in the same PR**.
      A test that only ran on your machine protects nobody.
- [ ] Anything you did NOT verify, say so explicitly in the PR body. An honest
      "synth not re-run" is fine; a silent gap is a violation.

## D. Tracker & claims honesty (catches: perfection_100, both inflation incidents)
- [ ] `skipped ≠ done`. `partial ≠ done`. Never flip a manifest checkpoint
      without the gate output in hand. If Mohamed asks for "100%", scope the
      claim ("Phase 2 is 100%") — never inflate the tracker to match a wish.
- [ ] Never claim compliance with a standard the code doesn't meet (the
      NeithCore "ML-KEM" Q=7681≠3329 lesson). Name what it actually is.
- [ ] Only `tools/gen_tracking.py` touches PROGRESS.md — never hand-edit
      generated files (same for `flow/gen_harden_results.py` → HARDEN_RESULTS.md).

## E. Phase-specific gates (the definition of done, per phase)
- **P2 RTL:** cocotb bit-exact vs the Python golden (not "looks right"),
  covering edge cases the golden covers; Yosys 0-latch; Verilator lint clean.
- **P3/P4 P&R:** WNS ≥ 0.00 AND 0 route-DRC from the actual ORFS reports;
  regenerate HARDEN_RESULTS.md with the script; if timing needed a relaxed
  clock, SAY the new frequency in the PR — a closed-at-50MHz block is fine,
  a hidden relaxation is not.
- **P5 formal:** ALWAYS `async2sync` before `write_smt2` (vacuity bug);
  `grep -c assert` the emitted .smt2 must be > 0; mutation-test every new
  property (corrupt the RTL → proof must FAIL); grep smtbmc output for
  `"Status: PASSED"` not bare `PASSED`. No tautologies (a 6-bit counter
  "≤ 63" proves nothing).

## F. Security & robustness (RTL and tools)
- [ ] No secrets/tokens/keys in code, configs, logs, or test fixtures — ever.
- [ ] Python tools: no `eval`/`exec`/`shell=True` on external strings; use
      arg-lists for subprocess; `argparse` + stdlib only (dependency discipline).
- [ ] Crypto cores (Anubis/Neith): fixed-latency, no secret-dependent branches
      or memory addressing — verify and state it in the module header. Never
      invent crypto or "optimize" a crypto datapath in a way that makes timing
      data-dependent.
- [ ] Fail closed: on any script error, exit nonzero and stop — never fall
      through to a "PASS" print (this is exactly how vacuous proofs happened).

## G. Process (catches: direct-to-main pushes, wrong WORKLOG refs)
- [ ] Branch → PR for EVERYTHING, including one-line chores and doc edits.
- [ ] Start every arc from fresh pulled `main`; never build on a stale branch.
- [ ] WORKLOG entry per unit of work with the REAL commit hash and REAL PR
      number, written after the PR exists — never copy-paste a previous ref.
- [ ] Never self-merge outside all-green /goal gates; stop at PR for Mohamed.
- [ ] Re-read `docs/agent/AVOID_LIST.md` at the start of every session; when
      you make a NEW mistake, append it there in the same PR as the fix.

**The test for "am I done?": every sentence in your final summary points to a
command output that exists. If a sentence has no output behind it, either run
the command or delete the sentence.**
