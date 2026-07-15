# AVOID LIST — Mistakes Already Made Here (Do Not Repeat Them)

Every item below cost a real session's time or shipped a real bug in this repo.
Read the whole list before your first change. These are ordered by how badly they
hurt.

## A. Correctness & honesty (these are failed tasks, not style nits)

1. **Vacuous formal proofs.** 8 of 11 cores once "proved" properties while checking
   ZERO assertions, because `write_smt2` drops `$check` cells without `async2sync`
   first. → ALWAYS `async2sync` before `write_smt2`. ALWAYS `grep -c assert` the
   `.smt2` (>0). ALWAYS mutation-test (corrupt logic ⇒ proof FAILS).
2. **Claiming "done/works/fixed" without running it.** Forbidden. Run the gate,
   read the output, then report. "It should work" is a failure state.
3. **Inflating the tracker.** `partial` is not `done`. The strict % is honest on
   purpose (currently 34%). Do not flip a phase to `done` for breadth's sake.
4. **Editing a file you have not read this session.** Always read the target region
   (and its golden model + neighbours) first.
5. **Weakening a test to make it pass.** If cocotb is not bit-exact, your RTL is
   wrong — fix the RTL, never loosen the check.
6. **Changing a shared golden model to make a new feature pass.** e.g. the base
   `seth_rv32im.py` HALTS on `op==0x73`; changing that breaks ALL existing core
   tests. Add a subclass / new file instead (this is why `seth_rv32im_zicsr.py`
   exists as a behavior-preserving hook).

## B. Git / GitHub workflow

7. **Self-merging.** You may open PRs; you may NOT merge without Mohamed's explicit
   "merge". A generic "keep going" is not merge authorization.
8. **Committing to `main` directly.** It is branch-protected — it will reject you.
   Always branch.
9. **`gh pr edit` is BROKEN on this repo** (GraphQL "Projects classic deprecated").
   Use `gh api --method PATCH repos/Lord1Egypt/KemetCore/pulls/<N> -f title=..`.
10. **`gh pr update-branch` does not exist in this gh version.** Use
    `gh api --method PUT repos/Lord1Egypt/KemetCore/pulls/<N>/update-branch`.
11. **Detecting merge by grepping `gh pr merge` stdout.** Unreliable — a train once
    looped forever. Poll `gh pr view <N> --json state` for `MERGED`.
12. **Leaving work uncommitted.** Commit the instant a step verifies green. Push
    after every commit. Dirty trees lose work on a crash.
13. **Merging a stacked PR before its CI checks register.** Empty `gh pr checks`
    output is NOT green — it means checks haven't started. Wait for both required
    checks to appear AND pass.
14. **`git checkout main` while a background job owns the working tree.** Use a
    `git worktree` for parallel work.

## C. RTL / Yosys (v0.65) gotchas

15. **Yosys rejects unpacked-array function ports** (Verilator allows them) → keep
    round/loop logic in a module-level `always_comb`; use case-based ROM functions,
    not 2D-array assignment patterns.
16. **SV `inside` operator is unsupported by Yosys 0.65** (Verilator accepts it, so
    cocotb passes but synth parse-fails) → expand to explicit OR chains.
17. **`vectored` is a Verilog keyword** — do not use it as a signal name.
18. **1-bit signal `<< N` → WIDTHEXPAND** (fails the cocotb build) → zero-extend:
    `{31'd0, sig} << N`.
19. **Latch inferred on data-dependent array fill** → default-init every array
    element at the top of the `always_comb` before conditional writes.
20. **UNOPTFLAT on unpacked-array combinational chains** → use an `always_comb`
    scalar accumulator instead of chaining through an array.
21. **NaN sign is implementation-defined** (`inf + -inf`: numpy gives 0xFFC00000,
    the hardware fp-add gives 0x7FC00000) → compare NaN outputs **canonically**
    (via an `is_nan32`-style helper), not bit-for-bit.
22. **`run_synth.sh` must confirm 0 latches.** A synth that infers a latch is a bug,
    not a warning — fix the RTL.

## D. CI / testbench

23. **Substring collisions when guarding `ci.yml` edits.** `'CORE=norm' in
    'CORE=normalize'` and `'CORE=compress'` (neith vs geb) collide → guard on the
    FULL `run_sim.sh CORE=x` line, not a substring.
24. **cocotb is PINNED to 1.9.2** (2.x needs Verilator ≥5.036; the box has 5.020).
    Do not bump it.
25. **Only "Phase 0/1 tests" and "Phase 2 RTL" are REQUIRED checks.** The synth and
    formal jobs are informational. Do not wait on the wrong job; do not assume a
    green synth job means the PR is mergeable.

## E. Phase 4 P&R (Docker ORFS)

26. **Do not remove `LEC_CHECK=0`** from `flow/harden.sh` — without it CTS dies with
    `child killed: illegal instruction` (AVX-512 formal binary on a Coffee-Lake CPU).
27. **Do not `rm` ORFS output on the host** (permission denied — it runs as root) →
    clean via the container (see PLAYBOOK Part D).
28. **Do not commit a design that does not close timing** (WNS < 0) or does not
    route (nonzero DRC). Large flat designs hit the hold-buffer / RAM wall — they
    need SRAM-macro / hierarchical flow or a bigger box, not a forced commit.
29. **Never hand-type WNS/area/util into `HARDEN_RESULTS.md`** → it is generated by
    `flow/gen_harden_results.py` from the real reports.

## F. General discipline

30. **Do not add dependencies.** Standard library + the existing toolchain only.
31. **Do not over-engineer.** Smallest thing that works and verifies. No speculative
    abstractions, no unrelated refactors bundled into a feature PR.
32. **Do not guess on irreversible/architectural decisions.** Log a `NEEDS-MOHAMED`
    note in `WORKLOG.md` and work on something unblocked instead.
