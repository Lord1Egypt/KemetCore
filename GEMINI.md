# GEMINI.md

Antigravity / Gemini: your full operating contract for this repository is in
**[`AGENTS.md`](AGENTS.md)** at the repo root. Read it first, then the deep
playbook in **[`docs/agent/`](docs/agent/)**.

Quick pointers:

- **Model to use:** Gemini **3 Pro — High thinking** for all RTL / formal /
  debugging / git work (default). Gemini 3 Flash only for mechanical CI polling.
- **The loop:** orient → branch → read → build small → verify (cocotb bit-exact +
  Yosys 0-latch + formal) → `python tools/gen_tracking.py` → commit + log →
  PR → wait for Mohamed to say "merge".
- **Save after every step:** commit green work immediately, append to
  [`docs/agent/WORKLOG.md`](docs/agent/WORKLOG.md).
- **Never** claim it works without running it. **Never** self-merge without
  Mohamed's explicit "merge". **Never** commit a vacuous or non-mutation-tested
  formal proof.

Everything else — exact commands, toolchain paths, the full avoid-list, the task
menu, and the review checklist — is in `AGENTS.md` and `docs/agent/`.
