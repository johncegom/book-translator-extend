# Retrospective Log

Process, tooling and collaboration lessons that would change how a different future task is approached. Not for product bugs (`docs/BUGS.md`) or design tradeoffs (`docs/DECISIONS.md`), and not a per-task diary: task-specific notes go in that task's detail doc.

## RETRO-001: Check the whole test baseline before setting a "green" exit criterion

**What went well:** Running the suite first showed 22 environment failures before any code change, so Phase 1's "no test edits" rule has a measurable baseline.
**What could improve:** The plan assumed the suite was green on a clean clone. It was not on Windows, which cost a detour (skip list, CI setup). CI also did not start automatically on the first PR for reasons not found.
**Advice for next time:** Run the baseline in Phase 0 on the platform you actually use, and use CI as the second opinion. Treat a PR with "no checks reported" as a problem to investigate, not as a pass.
