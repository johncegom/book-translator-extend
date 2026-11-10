# Decision Log

## DECISION-001: Language profile layer instead of in-place Chinese → Vietnamese replacement

**Context:** Porting the translator to Vietnamese. Chinese-specific logic is spread across ~9 files, and 41 of 52 test files contain Chinese text or zh names.
**Decision:** Add `scripts/lang_profile.py`; all language-dependent behavior is read from a profile. `zh-tw` stays the default.
**Alternatives considered:** Search-and-replace port (breaks 41 test files, loses the safety net); quick fork (upstream changes often, hard to merge later).
**Consequences:** Phase 1 must pass all existing tests with no edits. One extra indirection in every consumer file. Upstream-mergeable.

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
