# Complete Exercise Solutions Implementation

**For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement each packet task-by-task. Use checkbox (`- [ ]`) steps.

**Goal:** Deliver canonical Python 3.10 answers, documentation, tests, and automated quality gates for all 56 repository exercises.

**Architecture:** Shared repository tooling is established first. Thirteen file-disjoint chapter packets then execute in waves of at most three workers, with specification and quality review after every packet and full integration checks after every wave.

**Tech Stack:** Python 3.10 and 3.14, uv, pytest, Ruff, Pyrefly, mypy, Pyright, Lefthook, GitHub Actions.

---

## Plan Set

Execute these plans in order:

1. `2026-07-28-foundation-tooling.md`
2. `2026-07-28-ch02-interactive.md`
3. `2026-07-28-ch04-ch05-collections-functional.md`
4. `2026-07-28-ch06-tracking-memoization.md`
5. `2026-07-28-ch06-ch07-decorators-generators.md`
6. `2026-07-28-ch08-metaclasses.md`
7. `2026-07-28-ch09-ch10-typing-testing.md`
8. `2026-07-28-ch11-ch12-debugging-performance.md`
9. `2026-07-28-ch13-asyncio.md`
10. `2026-07-28-ch14-ipc-files.md`
11. `2026-07-28-ch14-workers-rpc-parallel.md`
12. `2026-07-28-ch15-ch16-scientific-nlp.md`
13. `2026-07-28-ch17-native.md`
14. `2026-07-28-ch18-packaging.md`

## Execution Waves

- [ ] **Execution preflight:** Invoke `superpowers:using-git-worktrees` and
  create an isolated `codex/complete-exercise-solutions` worktree from the
  commit containing this complete plan set. Run every subsequent task from that
  worktree.
- [ ] **Wave 0:** Execute foundation tooling and verify configuration parsing,
  dependency locking, hooks, and CI syntax.
- [ ] **Wave 1:** Execute Chapter 2, Chapters 4-5, and Chapter 6 exercises 1-4
  concurrently.
- [ ] **Wave 1 review:** Run specification review per packet, then run the full
  canonical Ruff, Pyrefly, mypy, Pyright, and pytest commands.
- [ ] **Wave 2:** Execute Chapter 6 exercises 5-7 plus Chapter 7, Chapter 8, and
  Chapters 9-10 concurrently.
- [ ] **Wave 2 review:** Repeat packet reviews and all repository quality gates.
- [ ] **Wave 3:** Execute Chapters 11-12, Chapter 13, and Chapter 14 exercises
  1-2 concurrently.
- [ ] **Wave 3 review:** Repeat packet reviews and all repository quality gates.
- [ ] **Wave 4:** Execute Chapter 14 exercises 3-7, Chapters 15-16, and Chapter
  17 concurrently.
- [ ] **Wave 4 review:** Repeat packet reviews and all repository quality gates,
  including native and notebook integration markers.
- [ ] **Wave 5:** Execute Chapter 18.
- [ ] **Wave 5 review:** Run packaging integration checks and all repository
  quality gates.

## Final Integration

- [ ] Run `uv lock --check` and expect exit code 0.
- [ ] Run `uv sync --locked --all-groups` with Python 3.10 and expect exit code
  0.
- [ ] Run `uv run ruff format --check .` and expect exit code 0.
- [ ] Run `uv run ruff check .` and expect exit code 0.
- [ ] Run `uv run pyrefly check` and expect zero errors.
- [ ] Run `uv run mypy .` and expect `Success: no issues found`.
- [ ] Run `uv run pyright` and expect zero errors.
- [ ] Run `uv run pytest` and expect all tests to pass with no unexplained
  skips.
- [ ] Run the same pytest suite under Python 3.14 with
  `uv run --python 3.14 pytest` and expect all tests to pass.
- [ ] Confirm `pgrep -af 'mastering-python-exercises'` finds no leaked worker,
  server, or notebook processes.
- [ ] Run `git status --short` and confirm only intended tracked changes remain.
- [ ] Request independent code review with
  `superpowers:requesting-code-review`; return verified findings to the owning
  packet worker.
- [ ] Invoke `superpowers:verification-before-completion` and rerun every
  acceptance command before making a completion claim.
