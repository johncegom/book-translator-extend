# Task: Phase 1 — Language profile with zh-tw only

Status: done 2026-11-11 (all sub-tasks; PR #4, commit f111738 plus the CI result below). DoD approved by the user 2026-11-11, after a Fable review (19 findings, verdict "approve with changes") was folded in. Call Advise once for the whole Phase 1 field set before 1.2 (CLAUDE.md).

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
- [x] No existing test or config file is changed: `git diff --diff-filter=MDRT --name-only bb0eb35 -- test/ conftest.py requirements-dev.txt requirements.txt .github/` prints nothing. New files are allowed only under `test/golden/` and as `test/test_lang_profile.py`.
- [x] `pytest -q --ignore=test/golden --ignore=test/test_lang_profile.py` gives 438 passed, 269 skipped, 0 failed on Windows. The same command on the CI ubuntu job gives the same passed/skipped counts as the CI run on `bb0eb35` (record both in Notes).
- [x] Full `pytest -q` gives 438 + N passed (N recorded in Notes), 0 failed, 269 skipped.
- [x] CI is green on the PR (ubuntu py 3.10/3.12, windows py 3.12).

Golden (ground-truth) tests, under `test/golden/`
- [x] Characterization tests call existing entry points and pass at `bb0eb35` (run in the worktree) and after every conversion step. Each golden file records the command that derived it in a header comment.
- [x] Profile-API tests (`test/test_lang_profile.py`) fail with ImportError/AttributeError before 1.2 and pass after. Evidence: the test commit precedes the implementation commit.
- [x] Golden coverage, each pinned separately:
  - structural and contents label tables, `prefix_labels`, the footnote label, the AUP note text
  - `_target_long` for `zh-tw`, `zh-cn`, `en`, `ja`, `ko`, `"ZH-TW"` (case-folded) and an unknown code (returned unchanged)
  - `_nav_display_label` and `_nav_zh_label`
  - the four Han checks, each on its own: `paragraph_classification.py:13` (U+4E00–9FFF), `translation_quality_audit.py:58` (adds U+3400–4DBF), `_contains_han` (`:74-75`), `assemble.py:280`. Samples: U+3400, U+4DBF, U+4E00, U+9FFF, U+3007, `。`, kana, Hangul, U+F900, an Extension B character, the empty string, mixed `English ｜ 中文`
  - `is_english_content` (50 chars, 20 letters / 35%), `untranslated_reason`, `_has_tgt_class` in both audits, the `"譯文："` special case, the length rule at 0.22 and its margins (`_TITLE_RATIO_MARGIN`, `_SHORT_SENTENCE_RATIO_MARGIN`), and the glossary register override

Behaviour
- [x] Frozen-book comparison: for one frozen zh-tw book dir, `assemble` and `audit_suite` run before and after give the same ordered member-name list and the same SHA-256 per member, and the same audit output text. A first pair of runs on unchanged code proves the comparison itself is stable (zip member timestamps differ, so the `.epub` bytes are not compared).
- [x] The zh-tw data is defined once, in `lang_profile.py`. Existing module-level names and signatures stay as thin aliases or defaults resolving to the zh-tw profile (e.g. `dispatch.SUBAGENT_PROMPT_TEMPLATE`, `_nav_zh_label`, `missing_nav_zh_warnings`, `tqa._contains_han`, `contains_simplified_chinese`, the `assemble.py` re-exports), so no existing test needs an edit. Every new `profile` parameter defaults to zh-tw.
- [x] `_target_long` keeps its table and fallback; the profile supplies only the zh-tw long name.
- [x] Grep gate: after the change, `grep -nP '[\x{3400}-\x{9fff}]|zh-Hant|tgt-zh' scripts/{assemble,nav_builder,opf_builder,bilingual_rewriter,paragraph_classification,bilingual_coverage_audit,translation_quality_audit,glossary}.py` matches only comments, docstrings, the out-of-scope Simplified gate, and an allow-list recorded in Notes. `dispatch.py` is checked the same way for `build_subagent_prompt` and its template only.
- [x] Scope guard: `git diff bb0eb35 -- scripts/translate_book_ollama.py scripts/offline_postprocess.py scripts/translate_chapter_cli.py scripts/providers/` prints nothing.

Plumbing
- [x] `assemble` and `audit_suite.run_all` read `target_lang` from `<book_dir>/state.json`; a missing file or key means `zh-tw`. Each audit's `run`/`audit` gains an optional `profile` argument defaulting to zh-tw; CLI flags unchanged.
- [x] `get_profile(code)` is registered for `zh-tw` only; `get_profile` on an unknown code raises (this does not affect `_target_long`, which keeps its own fallback).
- [x] `LanguageProfile` (frozen dataclass, plain dict fields) has exactly these 13 fields in Phase 1 (amended 2026-11-11 after a Fable Advise call, user-approved): `code`, `long_name`, `html_lang` (`zh-Hant`; `nav_builder`, `opf_builder`), `target_class` (`tgt-zh`; `bilingual_rewriter`), `structural_labels`, `contents_labels`, `prefix_labels`, `footnote_label` (`註腳 {n}`), `bilingual_edition_label` (`中英對照`), `aup_refused_notice` (the sentence only), `prompt_rules`, `default_custom_instructions`, `is_target_text` (a callable field). Other fields wait for Phase 2/3. Profiles are compared by `.code`, never by identity or `==`.
- [x] `resolve_profile(code)` casefolds and falls back to zh-tw for any unregistered code; `build_subagent_prompt` and `assemble` use it, so the pinned `zh-cn` / `en` prompt output is unchanged. A DECISION entry records the fallback (to be tightened in Phase 2).
- [x] Guard test in `test/test_lang_profile.py`: a sentinel profile built with `dataclasses.replace(ZH_TW, ...)` (no Han, no `zh-Hant`, class `tgt-sentinel`) is passed to `insert_bilingual`, `build_nav_xhtml`, the OPF builder and both audits; the output contains no Han, `zh-Hant` or `tgt-zh`. Any helper that silently falls back to zh-tw fails the test.
- [x] `is_target_text` replaces the three checks over U+4E00–U+9FFF: `paragraph_classification.py:13`, `translation_quality_audit.py:75` (`_contains_han`) and `assemble.py:280`, plus their coverage-audit uses. `translation_quality_audit.py:58` (adds U+3400–4DBF) and the Simplified gate stay.
- [x] `_AUP_NOTE_HTML_TEMPLATE` is built by concatenation so `{reason}` survives the move (pinned in the golden file).
- [x] Grep-gate allow-list (recorded in Notes): `未命名` (`nav_builder._nav_label`, no production caller), the glossary prompt fragments (`glossary.py:62-83`), `GENERIC_SUBAGENT_RULES` (`dispatch.py:95`), `format_fixed_terms` (`dispatch.py:285`, ollama path), the assemble error text and the `bilingual_coverage_audit.py:73` message (no Han), the `｜` separator, and the two `\u` escapes the gate cannot see (`paragraph_classification.py:13`, `translation_quality_audit.py:58`; checked by hand).

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
- Types/interfaces: `LanguageProfile` frozen dataclass; `get_profile(code)` (strict, raises on unknown); `resolve_profile(code)` (casefolds, falls back to zh-tw); `ZH_TW`. Decide before 1.2: helpers take an optional `profile` argument defaulting to zh-tw (chosen, to keep direct test calls working); entry points resolve the profile once from `state.json` and pass it down.
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
- [x] 1.1b Golden cases derived from the `bb0eb35` worktree; characterization tests committed green before any code change
- [x] 1.2 Advise call done (Fable, one-time override, logged); `test/test_lang_profile.py` committed red first (`3e49f3e`), then `scripts/lang_profile.py` (`e949cf5`). Registry/shape tests are green; the 7 sentinel guard tests stay red until their consumer is converted in 1.3
- [x] 1.3 Consumers converted leaf-first, one commit each, suite + snapshot checked after each: paragraph_classification, bilingual_rewriter, nav_builder, opf_builder, assemble (+ archive_writer plumbing), bilingual_coverage_audit, translation_quality_audit, audit_suite, dispatch (subagent prompt only). glossary deliberately deferred (DoD allow-list).
- [x] 1.4 Verify the DoD (diff checks, grep gate, hashes, scope guard, CI green); update `docs/LEDGER.md`

## Notes / deviations
- Plan fix: the audit's length-rule default is 0.22 (`translation_quality_audit.py:80,95`), not 30%.
- 1.1a (done): `frozen-fixture/` holds hand-written Traditional Chinese translations for an Alice excerpt (title page in full; chapters I and II as heading plus first 5 and 4 paragraphs), `state.json`, `glossary.json`, `translations_extra.json`, `build.py` and `snapshot.py`. Build and snapshot:
  - `python docs/tasks/01-profile-zh-tw/frozen-fixture/build.py runs/alice/out/alice runs/alice/frozen`
  - `python docs/tasks/01-profile-zh-tw/frozen-fixture/snapshot.py runs/alice/frozen runs/alice/alice.epub <snapshot.json>`
  - Baseline (code identical to `bb0eb35`; `git diff bb0eb35 -- scripts` was empty): 22 zip members, audit_suite exit 1. Two runs on unchanged code produced byte-identical snapshots, so the comparison is stable. Local copy at `runs/alice/baseline_bb0eb35.json` (gitignored).
  - The audit FAILs by design on this excerpt: `bilingual_coverage` reports the 10 untranslated chapters still carried in the output (about 600 lines), while `structural`, `translation_quality` and `href_resolve` PASS and the three translated items raise no coverage findings. That gives both a negative and a positive path; any change in that text is a regression signal.
- 1.1b (done): `test/golden/derive.py` computes the zh-tw values; `golden_zh_tw.json` is its output run inside a worktree of `bb0eb35` (`git worktree add ../bt-oracle bb0eb35`, then `python <repo>/test/golden/derive.py > <repo>/test/golden/golden_zh_tw.json`). `test_zh_tw_characterization.py` recomputes on the current code and compares group by group (9 groups: tables, target_long, han, paragraph, untranslated_reason, nav, rewriter, audit, prompt).
  - Verified: the 11 golden tests pass in the `bb0eb35` worktree and on this branch; `pytest -q --ignore=test/golden` is still 438 passed, 269 skipped; the DoD `--diff-filter=MDRT` check prints nothing. Mutation checks: changing a label (`Cover`) or shrinking the Han range by one code point (`鿿` to `鿾`) fails the `tables`/`nav` and `han` groups respectively.
  - Known gaps, deliberate: (1) the `assemble.py:280` Han regex is local to a function, so it is pinned only by the frozen-book snapshot; (2) `assets/register_hints.json` has one register with `min_length_ratio` (0.22), equal to the default, so a differing glossary override value cannot be pinned without changing assets; the ratio parameter itself is pinned at 0.22 and 0.3 in `reviewable_short_target`; (3) the frozen snapshot's 600-line coverage output also guards the audit text.
  - Keep the `../bt-oracle` worktree until Phase 1 is done, to re-derive if a golden test is ever questioned. Never regenerate the JSON from refactored code.
- 1.3 (done): suite after the last commit: 472 passed, 269 skipped (438 baseline + 34 new: 11 golden + 23 profile tests); frozen-book snapshot byte-identical to the `bb0eb35` baseline after every conversion commit; the 7 sentinel guard tests went green one consumer at a time.
- Grep-gate allow-list (what still matches `grep -nP '[\x{3400}-\x{9fff}]|zh-Hant|tgt-zh'`): comments and docstrings in `nav_builder`, `bilingual_rewriter`, `bilingual_coverage_audit`, `translation_quality_audit`; `未命名` in `nav_builder._nav_label` (no production caller); `BANNED_PATTERNS`, `SIMPLIFIED_CHINESE_CHARS`, `_HAN_RE` (the U+3400 range) and the `"譯文："` special case in `translation_quality_audit` (Simplified gate, out of scope); the glossary prompt fragments in `glossary.py` (lines 62-83, deferred); in `dispatch.py` `GENERIC_SUBAGENT_RULES`, `format_fixed_terms`, the ollama/minimal prompt constants, and the non-zh-tw rows of `_target_long`. The assemble error text and the "missing adjacent zh" message contain no Han and stay. The escape-written Han range now lives only in `lang_profile.HAN_RE` and `translation_quality_audit._HAN_RE` (checked by hand).
- Behaviour notes: `build_subagent_prompt(profile=None)` uses `resolve_profile(target_lang)` for the rules and `_target_long(target_lang)` for the display name, so the pinned `zh-cn`/`en` prompts are unchanged; an explicit profile supplies both. `SUBAGENT_PROMPT_TEMPLATE` and `DEFAULT_CUSTOM_INSTRUCTIONS` remain as zh-tw-rendered aliases. A profile's `prompt_rules` must not contain braces (it is substituted before `str.format`).
- Commit hygiene: three local commit messages briefly carried stray `EOF` / `)` lines from a shell heredoc slip; they were rewritten before pushing (unpushed commits only).
- 1.4 (done): CI run 42961118515 on `feat/lang-profile-zh-tw` (manual dispatch, because the draft PR's base is not `main` so `pull_request` did not fire): ubuntu 3.10, ubuntu 3.12 and windows 3.12 all green with 472 passed, 269 skipped. The baseline CI run at `bb0eb35` (run 42890688752) had 438 passed, 269 skipped on all three; 472 = 438 + 34 new tests, skipped unchanged. The old-subset command was run explicitly only on Windows locally (438 passed, 269 skipped); on ubuntu the equality is derived from the totals, not a separate run.
