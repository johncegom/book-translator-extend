# Task: Phase 1 — Language profile with zh-tw only

Status: not started. DoD below is a draft: review it before implementation, and call Advise before adding the first `LanguageProfile` field (see CLAUDE.md).

## Definition of Done
- [ ] `scripts/lang_profile.py` exists with `LanguageProfile` and `get_profile(code)`; only `zh-tw` is registered.
- [ ] Chinese labels, prompt rules and the Han check are moved into the `zh-tw` profile (no copies left in the consumer files).
- [ ] `target_lang` from `state.json` is passed through dispatch, assemble and the audits; the default stays `zh-tw`.
- [ ] `pytest -q` gives the same result as the Phase 0 baseline: 438 passed, 269 skipped, 0 failed.
- [ ] **No file under `test/` is modified** (check: `git diff --stat origin/main -- test/` is empty). A needed test edit means the refactor changed behaviour: stop and log it.
- [ ] CI is green on the PR.
- [ ] Ground-truth cases exist under `test/golden/` (new files), each derived by running the pre-refactor code at `bb0eb35` and recorded with the command used. Covered functions: label lookup (structural and contents), `_target_long("zh-tw")`, the Han check on a set of sample strings, `_nav_display_label`, and the audit predicates and thresholds in `bilingual_coverage_audit.py` and `translation_quality_audit.py`.
- [ ] Each golden test was run against the new profile path and seen to fail before the matching consumer was converted, then pass after.
- [ ] A zh-tw run on `runs/alice/` produces byte-identical `assemble` output before and after the change (compare against a copy made before starting).

## Test Plan
- Unit-tested: the existing suite is the test. No new Vietnamese tests in this phase.
- Ground-truth tests: derive first, then write the test, then implement (see CLAUDE.md, Ground-truth TDD). Record the derivation command in a comment at the top of each golden file.
- Added tests: only for `get_profile` itself (unknown code raises; `zh-tw` returns the expected labels). These are new files, not edits.
- Manually smoke-tested: assemble Alice with zh-tw before and after, diff the output directory.
- Commands: `pytest -q`; `git diff --stat origin/main -- test/`

## Program design
Fill because the change touches ~9 files whose interaction is not obvious.
- Types/interfaces: `LanguageProfile` frozen dataclass and `get_profile(code)` (fields as in the plan file). Phase 1 may use only the fields zh-tw needs; remaining fields wait for Phase 2/3 (proportionality).
- Call sites to change (from `grep`):
  - `dispatch.py`: `_target_long` table (~line 558) and the prompt rule text; callers at ~329, 371, 388.
  - `glossary.py`: prompt wording (~line 62); keep the `chapter_titles_zh` key (DECISION-002).
  - `bilingual_rewriter.py`: label dicts and class `"tgt-zh"` (~line 208).
  - `nav_builder.py`: prefix labels, the "footnote" word.
  - `paragraph_classification.py`: `HAN_RE` (lines 13, 28, 98) → `profile.is_target_text`.
  - `bilingual_coverage_audit.py`: `HAN_RE` (lines 62, 133, 159) and `"tgt-zh"` (148) → profile.
  - `translation_quality_audit.py`: `_HAN_RE` (58, 290), `"tgt-zh"` (271).
  - `state.py` (line 7) and `translate_chapter_cli.py` (line 76): keep default `zh-tw`, pass the code through.
- Call graph sketch: entry points read `target_lang` from state → `get_profile(target_lang)` once → pass the profile object down to dispatch/rewriter/audits. Consumers never import label tables directly.
- Package/file layout: single package (`scripts/`); one new module.

## Sub-tasks
- [ ] 1.1 Save a baseline assemble output of Alice (zh-tw) to compare against, and derive the golden cases from `bb0eb35`
- [ ] 1.2 Add `lang_profile.py` with the zh-tw profile
- [ ] 1.3 Convert consumers one file at a time, running `pytest -q` after each
- [ ] 1.4 Verify DoD (diff of `test/` empty, byte-identical output, CI green)

## Notes / deviations
