# Task: Phase 1 — Language profile with zh-tw only

Status: in progress (1.1a done). DoD approved by the user 2026-11-11, after a Fable review (19 findings, verdict "approve with changes") was folded in. Call Advise once for the whole Phase 1 field set before 1.2 (CLAUDE.md).

Oracle: `main` at `bb0eb35`. Derive every golden value from a worktree of that commit (`git worktree add ../bt-oracle bb0eb35`), never from memory.

## Scope

In: move the zh-tw-specific data and rules into `scripts/lang_profile.py`, keep behaviour identical.

Out (stay as they are in Phase 1):
- The ollama/omlx prompt constants and builders in `dispatch.py` (`OLLAMA_SYSTEM_PROMPT`, `MINIMAL_PARAGRAPH_SYSTEM_PROMPT`, callers at ~329 and ~371), `translate_chapter_cli.py`, `translate_book_ollama.py`, `offline_postprocess.py`, `providers/`. Their tests are skipped (DECISION-004), so a change there would be invisible.
- The Simplified-Chinese gate in `translation_quality_audit.py`: `_HAN_RE`, the count-of-8 rule, `SIMPLIFIED_CHINESE_CHARS`, `BANNED_PATTERNS`, the `ambiguous_simplified_fixes` import.
- Phase 3 items: `is_untranslated_source`, the echo check, a profile-level `min_length_ratio`.
- `chunker.py` token budget (note for Phase 3). `build_terms.py` (decide in Phase 2 whether it is on the subagent path).

## Definition of Done

Tests and baseline
- [ ] No existing test or config file is changed: `git diff --diff-filter=MDRT --name-only bb0eb35 -- test/ conftest.py requirements-dev.txt requirements.txt .github/` prints nothing. New files are allowed only under `test/golden/` and as `test/test_lang_profile.py`.
- [ ] `pytest -q --ignore=test/golden --ignore=test/test_lang_profile.py` gives 438 passed, 269 skipped, 0 failed on Windows. The same command on the CI ubuntu job gives the same passed/skipped counts as the CI run on `bb0eb35` (record both in Notes).
- [ ] Full `pytest -q` gives 438 + N passed (N recorded in Notes), 0 failed, 269 skipped.
- [ ] CI is green on the PR (ubuntu py 3.10/3.12, windows py 3.12).

Golden (ground-truth) tests, under `test/golden/`
- [ ] Characterization tests call existing entry points and pass at `bb0eb35` (run in the worktree) and after every conversion step. Each golden file records the command that derived it in a header comment.
- [ ] Profile-API tests (`test/test_lang_profile.py`) fail with ImportError/AttributeError before 1.2 and pass after. Evidence: the test commit precedes the implementation commit.
- [ ] Golden coverage, each pinned separately:
  - structural and contents label tables, `prefix_labels`, the footnote label, the AUP note text
  - `_target_long` for `zh-tw`, `zh-cn`, `en`, `ja`, `ko`, `"ZH-TW"` (case-folded) and an unknown code (returned unchanged)
  - `_nav_display_label` and `_nav_zh_label`
  - the four Han checks, each on its own: `paragraph_classification.py:13` (U+4E00–9FFF), `translation_quality_audit.py:58` (adds U+3400–4DBF), `_contains_han` (`:74-75`), `assemble.py:280`. Samples: U+3400, U+4DBF, U+4E00, U+9FFF, U+3007, `。`, kana, Hangul, U+F900, an Extension B character, the empty string, mixed `English ｜ 中文`
  - `is_english_content` (50 chars, 20 letters / 35%), `untranslated_reason`, `_has_tgt_class` in both audits, the `"譯文："` special case, the length rule at 0.22 and its margins (`_TITLE_RATIO_MARGIN`, `_SHORT_SENTENCE_RATIO_MARGIN`), and the glossary register override

Behaviour
- [ ] Frozen-book comparison: for one frozen zh-tw book dir, `assemble` and `audit_suite` run before and after give the same ordered member-name list and the same SHA-256 per member, and the same audit output text. A first pair of runs on unchanged code proves the comparison itself is stable (zip member timestamps differ, so the `.epub` bytes are not compared).
- [ ] The zh-tw data is defined once, in `lang_profile.py`. Existing module-level names and signatures stay as thin aliases or defaults resolving to the zh-tw profile (e.g. `dispatch.SUBAGENT_PROMPT_TEMPLATE`, `_nav_zh_label`, `missing_nav_zh_warnings`, `tqa._contains_han`, `contains_simplified_chinese`, the `assemble.py` re-exports), so no existing test needs an edit. Every new `profile` parameter defaults to zh-tw.
- [ ] `_target_long` keeps its table and fallback; the profile supplies only the zh-tw long name.
- [ ] Grep gate: after the change, `grep -nP '[\x{3400}-\x{9fff}]|zh-Hant|tgt-zh' scripts/{assemble,nav_builder,opf_builder,bilingual_rewriter,paragraph_classification,bilingual_coverage_audit,translation_quality_audit,glossary}.py` matches only comments, docstrings, the out-of-scope Simplified gate, and an allow-list recorded in Notes. `dispatch.py` is checked the same way for `build_subagent_prompt` and its template only.
- [ ] Scope guard: `git diff bb0eb35 -- scripts/translate_book_ollama.py scripts/offline_postprocess.py scripts/translate_chapter_cli.py scripts/providers/` prints nothing.

Plumbing
- [ ] `assemble` and `audit_suite.run_all` read `target_lang` from `<book_dir>/state.json`; a missing file or key means `zh-tw`. Each audit's `run`/`audit` gains an optional `profile` argument defaulting to zh-tw; CLI flags unchanged.
- [ ] `get_profile(code)` is registered for `zh-tw` only; `get_profile` on an unknown code raises (this does not affect `_target_long`, which keeps its own fallback).
- [ ] `LanguageProfile` has only the fields zh-tw needs in Phase 1: `code`, `long_name`, `target_class`, `structural_labels`, `contents_labels`, `prefix_labels`, `prompt_rules`, `is_target_text`. Other fields wait for Phase 2/3.

## Test Plan
- Unit/characterization: existing suite plus `test/golden/` (derive first, then write the test, then implement; see CLAUDE.md, Ground-truth TDD).
- Frozen-book check is local-only (`runs/` is gitignored); paste the hash and audit diff result into Notes. Note that `test_e2e.py` and `test_audit_suite.py` skip unless `animal_farm.epub` exists in the author's old path, so no committed test covers assemble end to end; this check is the only coverage.
- Commands:
  - `pytest -q`
  - `pytest -q --ignore=test/golden --ignore=test/test_lang_profile.py`
  - `git diff --diff-filter=MDRT --name-only bb0eb35 -- test/ conftest.py requirements-dev.txt requirements.txt .github/`
  - `git diff bb0eb35 -- scripts/translate_book_ollama.py scripts/offline_postprocess.py scripts/translate_chapter_cli.py scripts/providers/`
  - the grep gate above

## Program design
Fill because the change touches many files whose interaction is not obvious.
- Types/interfaces: `LanguageProfile` frozen dataclass; `get_profile(code)`. Decide before 1.2: helpers take an optional `profile` argument defaulting to zh-tw (chosen, to keep direct test calls working); entry points resolve the profile once from `state.json` and pass it down.
- Call sites (`path:line` from the review of `bb0eb35`):
  - `paragraph_classification.py:13,28,98`: Han predicate (U+4E00–9FFF).
  - `bilingual_rewriter.py:17-43` (label tables), `:51` (AUP note), `:208` (`["tgt", "tgt-zh"]`).
  - `nav_builder.py:79` (`zh-Hant`), `:81`, `:85`, `:203-205` (prefix labels), `:215` (footnote), `:266` (`未命名`).
  - `opf_builder.py:56`: `<dc:language>zh-Hant</dc:language>`.
  - `assemble.py:28-48` (re-exports), `:111-115` (error text), `:280` and `:311-319` (local Han regex).
  - `bilingual_coverage_audit.py:62,73,133,148,159`; `translation_quality_audit.py:132,141,271` (the `{"tgt","tgt-zh"}` class sets already match neutral `"tgt"`, so only the rewriter at `:208` needs the profile).
  - `dispatch.py`: `build_subagent_prompt` (~388), template rule `:71-74`, `DEFAULT_CUSTOM_INSTRUCTIONS` `:85-89`, `GENERIC_SUBAGENT_RULES` `:95`, `format_fixed_terms` `:285`, `_target_long` `:558`.
  - `glossary.py:62-83`: prompt wording, lines 66, 75, 78-79, 83; the key `chapter_titles_zh` stays (DECISION-002).
  - `state.py:7`: default stays `zh-tw`.
- Call graph: entry point reads `target_lang` → `get_profile()` once → profile passed to the rewriter, nav, OPF, assemble and the audits. Consumers never import label tables directly except through the preserved aliases.
- Layout: single package (`scripts/`); one new module `lang_profile.py`.

## Sub-tasks
Conversion order is leaf first because `nav_builder` imports the rewriter's tables and `assemble` re-exports both. One commit per file; after each, run `pytest -q` and the frozen-book comparison. Open a draft PR after 1.2 so CI runs on every commit.
- [x] 1.1a Frozen zh-tw fixture built (option A, hand-written translations) and baseline recorded; see Notes. Files: `docs/tasks/01-profile-zh-tw/frozen-fixture/`
- [ ] 1.1b Derive golden cases from the `bb0eb35` worktree and commit the characterization tests green before any code change
- [ ] 1.2 Advise call for the Phase 1 field set; add `lang_profile.py` and the zh-tw profile (profile-API tests committed first, red)
- [ ] 1.3 Convert consumers in this order: `paragraph_classification` → `bilingual_rewriter` → `nav_builder` → `opf_builder` → `assemble` → `bilingual_coverage_audit` and `translation_quality_audit` → `dispatch` (`build_subagent_prompt` only) → `glossary`
- [ ] 1.4 Verify the DoD (diff checks, grep gate, hashes, scope guard, CI green); update `docs/LEDGER.md`

## Notes / deviations
- Plan fix: the audit's length-rule default is 0.22 (`translation_quality_audit.py:80,95`), not 30%.
- 1.1a (done): `frozen-fixture/` holds hand-written Traditional Chinese translations for an Alice excerpt (title page in full; chapters I and II as heading plus first 5 and 4 paragraphs), `state.json`, `glossary.json`, `translations_extra.json`, `build.py` and `snapshot.py`. Build and snapshot:
  - `python docs/tasks/01-profile-zh-tw/frozen-fixture/build.py runs/alice/out/alice runs/alice/frozen`
  - `python docs/tasks/01-profile-zh-tw/frozen-fixture/snapshot.py runs/alice/frozen runs/alice/alice.epub <snapshot.json>`
  - Baseline (code identical to `bb0eb35`; `git diff bb0eb35 -- scripts` was empty): 22 zip members, audit_suite exit 1. Two runs on unchanged code produced byte-identical snapshots, so the comparison is stable. Local copy at `runs/alice/baseline_bb0eb35.json` (gitignored).
  - The audit FAILs by design on this excerpt: `bilingual_coverage` reports the 10 untranslated chapters still carried in the output (about 600 lines), while `structural`, `translation_quality` and `href_resolve` PASS and the three translated items raise no coverage findings. That gives both a negative and a positive path; any change in that text is a regression signal.
