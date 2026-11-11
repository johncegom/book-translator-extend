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

## DECISION-006: Unknown target codes fall back to zh-tw (`resolve_profile`), `get_profile` stays strict

**Context:** The golden file pins the zh rule text in the subagent prompt for `zh-cn` and `en` too, and `assemble` ignores `target_lang` today. A strict lookup in those paths would change behaviour.
**Decision:** `lang_profile.get_profile(code)` raises `ValueError` on an unregistered code. `resolve_profile(code)` casefolds and returns the zh-tw profile for any unregistered code, including `None` and `""`. Existing entry points (`build_subagent_prompt`, `assemble`, the audits) use `resolve_profile`.
**Alternatives considered:** Strict everywhere (changes pinned `zh-cn`/`en` prompts and breaks callers that pass other codes); silent default with no strict variant (no way to reject a typo like `vi ` once Vietnamese exists).
**Consequences:** In Phase 1 a mistyped code silently produces zh-tw output, as it does today. Phase 2 must tighten this once `vi` is registered (at least reject codes for which no profile exists, in `assemble` and the CLI).

## DECISION-007: LanguageProfile has 13 fields in Phase 1

**Context:** The first DoD listed 8 fields, which could not satisfy the grep gate (the `zh-Hant`, footnote, edition and AUP strings live in nav, OPF and rewriter). A Fable Advise call (2026-11-11, see `docs/eagd-log.md`) recommended the larger set.
**Decision:** `code`, `long_name`, `html_lang`, `target_class`, `structural_labels`, `contents_labels`, `prefix_labels`, `footnote_label`, `bilingual_edition_label`, `aup_refused_notice`, `prompt_rules`, `default_custom_instructions`, `is_target_text`. Plain dict fields in a frozen dataclass. Profiles are compared by `.code`, not identity. Helpers keep optional `profile` arguments that default to zh-tw, backed by a sentinel-profile guard test.
**Alternatives considered:** The 8-field set plus a relaxed gate (leaves `lang="zh-Hant"` and `註腳 N` in a Vietnamese nav); a read-only mapping type (breaks sharing the same object with the legacy module-level names and the JSON dump).
**Consequences:** Phase 2 mostly adds a second profile. Glossary prompt fragments, `GENERIC_SUBAGENT_RULES` and `format_fixed_terms` stay on the allow-list until Phase 2.
