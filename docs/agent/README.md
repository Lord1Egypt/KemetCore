# docs/agent/ — Instructions for AI Coding Agents

Start at the repo root **[`AGENTS.md`](../../AGENTS.md)** (auto-loaded by
Antigravity / Gemini). This folder is the deep detail behind it.

| File | What it is |
|------|------------|
| [`RESUME.md`](RESUME.md) | **"continue kemetcore" starts here** — current state + exact next step. Read at session start, overwrite at session end. |
| [`PLAYBOOK.md`](PLAYBOOK.md) | Every step with exact commands + toolchain paths. The ground truth for how to work. |
| [`AVOID_LIST.md`](AVOID_LIST.md) | Every mistake already made in this repo. Read before your first change. |
| [`TASK_MENU.md`](TASK_MENU.md) | What to work on next, tractable items first. |
| [`REVIEW_CHECKLIST.md`](REVIEW_CHECKLIST.md) | Run before calling anything done; it's also what the reviewer runs. |
| [`WORKLOG.md`](WORKLOG.md) | Append-only. Log every step here — this is what Mohamed audits. |

**The five rules that never bend:**
1. Never claim it works without running it and reading the output.
2. Verify every RTL change bit-exact vs golden + Yosys 0-latch; every formal proof
   non-vacuous + mutation-tested.
3. Commit + log after every green step. Never leave work dirty.
4. Never self-merge — open the PR, get CI green, wait for Mohamed's explicit "merge".
5. Honest tracker — `partial` ≠ `done`.

**Model:** Gemini 3 Pro (High thinking) for all real work; Flash only for CI polling.
