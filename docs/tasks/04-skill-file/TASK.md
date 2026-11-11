# Task: Phase 4 — The skill file (`SKILL.md`) and the fixes scheduled for it

Status: in progress. DoD and Test Plan approved by the user 2026-11-12; open-question answers recorded below.

Depends on: Phase 3 (PR #7, CI green, unmerged at the time of writing). Plan: `docs/plans/2026-11-11-vietnamese-language-profile.md` (Phase 4: Vietnamese trigger phrases, a step that asks for the target language, remove or make optional the `agent-orch` quota line; done when a fresh Claude Code session runs the skill with `vi` without manual fixes). Bugs scheduled here (`docs/BUGS.md`): BUG-001 (decide), BUG-002, BUG-003. Decision carried from Phase 2: `build_terms.py` is not available for `vi`.

## Findings from reading `SKILL.md` and the scripts at Phase 3

1. `SKILL.md` is 1168 lines; 211 of them contain Chinese. The frontmatter `description`, the Triggers list and the `target_lang` line in Step 1 are all zh-tw only. Step 1 never asks the user for a language: `target_lang` defaults to `zh-tw`.
2. **No script writes `target_lang` into `state.json`.** `assemble.py` and `audit_suite.py` only read it (a missing key means zh-tw). So the orchestrating session must write it, and `SKILL.md` has to say so; otherwise a `vi` run assembles and audits as zh-tw. Likewise Step 6 must pass `target_lang` to `dispatch.build_subagent_prompt(...)`. (Found by grep for `target_lang` in `scripts/`; `state.py` was not read line by line.)
3. Lines 58-59 hard-code `/Users/fredchu/bin/agent-orch quota check ...`, a path on the upstream author's machine, as an automatic step of the Anthropic path. It does not exist here.
4. The glossary key stays `chapter_titles_zh` (DECISION-002); the `SKILL.md` examples show `第一章`, which would mislead a `vi` run.
5. `build_terms.py` (term review, lines ~1047-1110) has a mandatory OpenCC/Simplified check that raises `RuntimeError` for non-zh. `offline_postprocess.py` (opencc s2tw) is also zh-only. The ollama, omlx and cloud-GPU engines were left out of the profile work (Phase 2 scope guard).
6. Evidence for the BUG-001 decision: *Subtract*'s `toc.ncx` points into the big files with fragment anchors (`index_split_000.html#p23`, `#p42`, `#p63`; `index_split_001.html#p91`, and so on: 22 entries over 3 files), and the targets are `<a id="pN">` elements in the files. So a split at the NCX targets is feasible for this book. Not checked: how many other EPUBs have this layout, or whether some have an NCX without anchors. The text also comes from `pdftohtml`: paragraphs are cut mid-sentence at page breaks (Phase 3 finding), which splitting by chapter does not fix.

## Proposed scope

A. **`SKILL.md` text**
- Frontmatter `description` and Triggers: add English and Vietnamese phrases ("dịch sách", "dịch ebook sang tiếng Việt", "translate this book to Vietnamese", "bilingual epub English-Vietnamese").
- Step 1: ask the target language (`AskUserQuestion`) with `zh-tw` and `vi` as the supported options; write `target_lang` to `state.json` at init; pass it to `build_subagent_prompt`. Unknown codes are already rejected by `assemble` and `audit_suite`.
- A short "Supported languages" table: `zh-tw` (all engines) and `vi` (Anthropic subagent path only). Say plainly that the offline engines, `offline_postprocess.py` and `build_terms.py` are zh-tw only, and that the skill must skip them for `vi`.
- Quota line: make the `agent-orch` gate optional ("run it only if the command exists"), not an automatic step.
- Examples that show `第一章` get a Vietnamese counterpart (`Chương 1: …`) next to them; the key name is explained once.
- Version bump 1.3.0 to 1.4.0.

B. **Bug fixes scheduled for this phase** (each with a test written first)
- BUG-002: a top-level `default_min_length_ratio` in `assets/register_hints.vi.json`, read by `_min_length_ratio_from_book_dir` when the register does not match; the zh-tw file has no such key, so it keeps 0.22. This changes the pinned Phase 2 test `test_min_length_ratio_for_vi_falls_back_to_the_default` (it asserts 0.22 for an unknown register under `vi`); that edit is a named carve-out and the only existing test that changes. An Advise call is required first (CLAUDE.md trigger 2: audit threshold); value 0.60 to match DECISION-012.
- BUG-003: the standalone `translation_quality_audit.py` CLI reads `target_lang` from `<book_dir>/state.json` like `audit_suite` does, and applies the profile and the register.

C. **BUG-001**: decision first, then (if a fix is chosen) the fix before Phase 5. See open question 1.

## Definition of Done (draft)

- [ ] `SKILL.md`: description and Triggers include English and Vietnamese phrases; Step 1 asks the target language; `target_lang` is written to `state.json` and passed to the prompt builder; the supported-languages table is present; `build_terms.py`, `offline_postprocess.py` and the offline engines are marked zh-tw only with an explicit "skip for `vi`" instruction; the `agent-orch` call is optional; version is 1.4.0.
- [ ] No Han is added to `vi`-specific instructions, and the zh-tw instructions keep their meaning (a diff review; every changed line is listed in this doc's results).
- [ ] BUG-002 fixed with tests: an unmatched register under `vi` gives 0.60; the zh-tw default stays 0.22; the carve-out test is the only existing test edited.
- [ ] BUG-003 fixed with tests: the CLI on a `vi` book dir uses the `vi` profile; without `state.json` it keeps zh-tw.
- [ ] BUG-001: the approach (a, b or c) recorded in `docs/DECISIONS.md` and the BUGS.md status updated. If (a) or (b) is chosen, the fix lands before Phase 5 (own PR or sub-task) with a test on a synthetic EPUB, not the copyrighted book.
- [ ] A scripted dry run of the skill's Phase 4 path on the Alice excerpt with `target_lang: vi`: `state.json` written, prompt built with Vietnamese rules and no Han, assemble and `audit_suite` run with the `vi` profile, no manual fix. (The plan's "fresh Claude Code session" check is manual and moves to Phase 5; see open question 3.)
- [ ] All Phase 1-3 checks hold: golden and frozen snapshots unchanged; `git diff --diff-filter=MDRT --name-only <phase-3 head> -- test/ ...` lists only the BUG-002 carve-out file; scope guard for the offline engines is empty.
- [ ] CI green (ubuntu 3.10/3.12, windows 3.12). Ledger updated; any new bug to `docs/BUGS.md`, tradeoffs to `docs/DECISIONS.md`.

## Test Plan

- Test-first for B (BUG-002, BUG-003): new `test/test_phase4_*.py`; commands `pytest -q` plus the frozen snapshot commands from Phase 3.
- `SKILL.md` is prose, so: one small structural pytest that reads it and asserts five things (the frontmatter has the new trigger phrases and the version, the supported-languages table exists, the `agent-orch` line is conditional, `build_terms.py` is marked zh-tw only, the Step 1 language question exists), plus a human diff review. Proportionality: keep it to these five.
- Dry run: a script in `docs/tasks/04-skill-file/` performing the steps above on `runs/alice/` (gitignored inputs); output recorded in a results section.
- Advise: one call before the BUG-002 default (threshold rule), logged. Not needed for the prose edits.

## Sub-tasks

- [x] 4.1 User approved the DoD and Test Plan 2026-11-12 (with the open-question answers)
- [x] 4.2 BUG-001 decision written (DECISIONS.md) and BUGS.md updated (DECISION-013)
- [x] 4.3 Red tests for BUG-002 and BUG-003; Advise call for the default ratio; fixes (done 2026-11-12: Advise opus logged; tests in test/test_phase4_bugs.py; carve-outs: test_lang_profile_vi.py and, from Phase 3, test_vi_length_ratio_phase3.py, the latter not an existing-test edit since it is newer than the gate commit)
- [x] 4.4 `SKILL.md` edits (A) and the structural test (SKILL.md edited, version 1.4.0; test/test_skill_md_phase4.py, 5 assertions)
- [x] 4.5 Dry run on the Alice excerpt; record results (docs/tasks/04-skill-file/dry_run.py; results below)
- [x] 4.6 BUG-001 fix if chosen (own PR or sub-task); verify DoD; ledger (code and tests done; CI and merge pending)

## Answers (user, 2026-11-12)

1. **BUG-001:** "a or b, depends on which will have better performance." Chosen: **(a)**, split at the NCX/nav fragment targets inside `extract_epub.py`. Reason: one pass over the spine files the extractor already reads; (b) would rewrite a whole EPUB and then extract it a second time. Fallback for an EPUB whose NCX has no anchors: today's behaviour (one item per spine file). Own PR, before Phase 5, test on a synthetic EPUB.
2. **Languages advertised:** `zh-tw` and `vi` only; expand later if ever needed.
3. **Fresh-session check:** moves to Phase 5 and is **run by the user**; I will ask them to do it then. Phase 4 uses the scripted dry run.
4. **Quota gate:** optional (run only if the command exists).

DoD change from the answers: the fresh-session item is not part of Phase 4; the BUG-001 item is fixed to approach (a).

## Open questions for you (original text)

1. **BUG-001 approach.** (a) split spine files at the NCX/nav fragment targets inside `extract_epub.py`; (b) a separate pre-split script before extraction; (c) document the limit and require pre-split EPUBs. I lean (a): the evidence above shows the *Subtract* NCX carries an anchor for every chapter, the extractor already owns the manifest, and (c) leaves Phase 5 without its book. Risk of (a): an EPUB whose NCX has no anchors still needs a fallback; keep today's behaviour (one item per spine file). Timing: before Phase 5, in its own PR so Phase 4 stays reviewable.
2. **Languages the skill advertises.** Only `zh-tw` and `vi`, or also mention that `zh-cn`, `en`, `ja`, `ko` fall back to the generic prompt without being supported end to end? I lean to advertise only the two that are tested.
3. **"Fresh session" check.** The plan's done-when is a fresh Claude Code session running the skill with `vi`. I propose the scripted dry run for Phase 4 and moving the fresh-session run into Phase 5, where a full book is translated anyway. Agree?
4. **Quota gate.** Make it optional (as drafted) or remove it from the skill? I lean optional, since removal drops a feature of the upstream workflow; but this repo is independent now, so removal is defensible.

## Results

### 4.4 SKILL.md edits
Version 1.3.0 to 1.4.0; frontmatter description and Triggers gain Vietnamese and English phrases; new "Supported languages" table (zh-tw, vi); the quota gate is conditional on `command -v agent-orch` and the personal path is gone; Step 1 asks the language with `AskUserQuestion` and writes it with `state.init_state(.., target_lang)` + `state.save`; Step 6 passes `target_lang=state["target_lang"]` to `build_subagent_prompt`; the Cloud mode, Offline mode and `build_terms.py` sections are marked zh-tw only with a skip instruction for `vi`. No Han text was added.

Correction to the draft finding 2: `state.init_state(book_path, spine, target_lang)` does write `target_lang`, but only the ollama driver calls it; the Anthropic flow in SKILL.md never said to, so the gap was in the prose, not in the scripts.

### 4.5 Dry run (`python docs/tasks/04-skill-file/dry_run.py`, copy of `runs/alice/frozen_vi`, state.json removed first)
- `state.json` written with `target_lang = vi`.
- Prompt built from `state["target_lang"]`: 3788 chars, Vietnamese rules present, 0 Han characters.
- `assemble.py` rc 0. `audit_suite.py`: structural PASS, translation_quality PASS, href_resolve PASS, bilingual_coverage FAIL only in the 10 files of chapters that have no translation (the fixture has 3 translated chapters); 0 failures inside translated chapters.
- Side finding: BUG-005 (coverage failure text says "adjacent zh" for vi).

## 4.6 Program design (BUG-001, chosen by the user 2026-11-12: "split items + assemble merge")

Why more than the extractor: `assemble.py` writes one output file per `original_path` (`replacements[original_path] = item_html`), so two items from one file would overwrite each other. The design keeps the output EPUB's files as they are.

- `extract_epub.py`: read the NCX (else the EPUB3 nav) and collect, per spine file, the fragment targets with their labels. A file is split only if at least two distinct targets land in different top-level children of `<body>`; otherwise nothing changes (one item, as today). Each segment is written to `chapters/item_NNN.html` as a full document (the original head plus its slice of the body). Item ids stay `item_{spine index + extra}`; `extra` grows by one per added segment, so an unsplit book keeps its ids byte for byte. The first segment also takes any content before the first target.
- `manifest.py`: `SpineEntry.fragment_id: str | None = None`, left out of `as_dict()` when None, so unsplit manifests are unchanged. The NCX label is the heading fallback for a segment that has no heading tag.
- `assemble.py`: a split entry reads its source from `href` (the segment), not from `original_path`; the rewritten segments of one original file are merged in order into that file's original document (head from the first segment, bodies concatenated); an unsplit entry follows the old path.
- `nav_builder.py`: the nav `<a href>` of a split entry gets `#fragment_id`.
- Known limit, not fixed here: `patch_toc_ncx` matches entries to NCX points by file name; with several entries per file all points of that file may get one label. It must not crash; logged as a bug if confirmed.

Tests (synthetic EPUB, test-first, `test/test_phase4_bug001_split.py`): split into the right segments with text preserved; no split without fragments, with one fragment, or when the targets share one wrapper element (manifest has no `fragment_id` key); ids stable for unsplit books; assemble round trip puts every segment, source and translation, in order inside one original file; nav href carries the fragment; Alice extract is unchanged (existing golden tests plus a manifest comparison with `main`).

### 4.6 Results
- `test/test_phase4_bug001_split.py`: 11 tests on a synthetic EPUB (split, no split without two usable targets, no split inside one wrapper, size threshold, ids, assemble round trip, nav fragments). Red before the code, green after.
- Alice: `diff -r` of the extract output before and after the change is empty (14 items).
- *Subtract* (local only): 23 items instead of 5, largest 84,236 characters; the body text of every original file equals the concatenation of its segments.
- Full suite: 668 passed, 269 skipped. Existing-test gate: nothing changed.
- Design change found while implementing: the first version split Alice too; DECISION-014 adds the 60,000-character floor.
