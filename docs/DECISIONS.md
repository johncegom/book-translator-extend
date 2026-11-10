# Decision Log

## DECISION-001: Language profile layer instead of in-place Chinese → Vietnamese replacement

**Context:** Porting the translator to Vietnamese. Chinese-specific logic is spread across ~9 files, and 41 of 52 test files contain Chinese text or zh names.
**Decision:** Add `scripts/lang_profile.py`; all language-dependent behavior is read from a profile. `zh-tw` stays the default.
**Alternatives considered:** Search-and-replace port (breaks 41 test files, loses the safety net). A hard fork is no longer a merge concern: this repo is independent of upstream (see CLAUDE.md), so the profile is justified by the test safety net alone.
**Consequences:** Phase 1 must pass all existing tests with no edits. One extra indirection in every consumer file. No upstream-merge constraint.

## DECISION-002: Keep glossary key `chapter_titles_zh`

**Context:** The key name is Chinese-specific but used across many files.
**Decision:** Keep it for all target languages.
**Alternatives considered:** Rename to a neutral key (touches many files, no functional gain).
**Consequences:** Name is slightly misleading for `vi`; acceptable.

## DECISION-003: Vietnamese detection via Vietnamese-only letters, paragraphs ≥ 50 chars

**Context:** Chinese is detected by script (Han); Vietnamese shares Latin letters with English.
**Decision:** A paragraph counts as Vietnamese if it contains Vietnamese-only letters (ă â đ ê ô ơ ư or tone-marked vowels), applied only at ≥ 50 chars, plus an echo check (translation == source fails) and a re-measured length ratio.
**Alternatives considered:** Language-ID library (new dependency, not evaluated); not decided beyond this heuristic.
**Consequences:** Short lines ("OK.") are not judged. Known weak spot: dialogue-heavy books. Test the "café" false-positive case in Phase 3.

## DECISION-004: Skip cloud-GPU and local-model tests; use GitHub CI as the test environment

**Context:** Phase 0 baseline on Windows gave 22 failures, all in cloud-GPU test files (bash and CRLF issues). The Vietnamese port covers only the Claude Code subagent path. The author's machine is too weak for WSL.
**Decision:** A root `conftest.py` skips the cloud-GPU and local-model (ollama/omlx) test files. The baseline is whatever `pytest -q` gives with those skipped (438 passed, 269 skipped on Windows). GitHub Actions (`.github/workflows/test.yml`, ubuntu + macOS) is the reference environment.
**Alternatives considered:** Fix the 22 failures (out-of-scope code); mark them Windows-only skips (hides the real cause); run WSL locally (machine too weak).
**Consequences:** Cloud and local paths are untested in this repo until the skip list is edited. They may rot, which is accepted. The skip list lives in `conftest.py`.

## DECISION-005: Slim CI to ubuntu, Python 3.10 + 3.12

**Context:** The inherited workflow ran ubuntu and macOS across Python 3.10-3.12 (6 jobs). The macOS runners existed for the upstream author's machine. The port targets the Claude Code subagent path, and we develop on Windows without WSL, so CI is the only Linux environment.
**Decision:** ubuntu-latest with Python 3.10 (documented minimum) and 3.12 (target), plus one windows-latest job on 3.12 because the author develops on Windows. Add concurrency cancel, read-only permissions, a 10-minute timeout and `workflow_dispatch`.
**Alternatives considered:** Keep macOS (slower, scarcer runners, no one here uses it); a single Python version (misses 3.10 syntax breakage); full Windows matrix (one Python is enough to catch OS-specific breakage).
**Consequences:** macOS-only regressions would go unseen. No CD exists or is needed: this is a skill, not a deployed service.
