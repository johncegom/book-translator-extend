# Bug Log

Entry format: symptom, root cause (or "unknown"), reachability, options, status. Logging is not fixing — wait for an explicit decision before applying a fix.

Candidates from the Vietnamese plan, to log only if they actually occur: short-paragraph detection gaps; English text with a single accented letter (e.g. "café") misclassified as Vietnamese.

## At a glance

Each entry below starts with a `STATE:` line. Read that line first; the long `Status:` line further down is the history.

States: FIXED (done, merged) / FIXED ON BRANCH (done, PR not merged) / FIXED, WITH A LIMIT / PARTLY FIXED / CLOSED (documented, no code change) / OPEN - NEEDS DECISION / OPEN - DECIDED, NOT STARTED / OPEN - NO FIX PLANNED.

| Bug | State | Title |
|---|---|---|
| BUG-001 | FIXED | EPUBs that pack several chapters into one spine file extract as a few huge items |
| BUG-002 | FIXED | A vi book whose glossary register matches no hint phrase is audited with min_length_ratio 0.22 |
| BUG-003 | FIXED | The standalone `translation_quality_audit.py` CLI ignores the profile |
| BUG-004 | OPEN - NO FIX PLANNED | A dispatch `register_override` changes the prompt but not the audit's length threshold |
| BUG-005 | FIXED | The coverage audit's failure text says "adjacent zh" for every language |
| BUG-006 | FIXED | `source_only` items inside a split file are not exempted from the coverage and quality audits |
| BUG-007 | FIXED | NCX table of contents is mostly English-only for books with split files |
| BUG-008 | PARTLY FIXED | A technical vi book keeps a few English-only labels in the output EPUB |
| BUG-009 | CLOSED - DOCUMENTED, NOT FIXED IN CODE | Reference-list and URL paragraphs are not exempted automatically in a vi book |
| BUG-010 | FIXED, WITH A LIMIT | `state.json` has no protection against concurrent writers |
| BUG-011 | FIXED, WITH A LIMIT | A reply with no `[[PARA_n]]` markers passes `validate_translation` but crashes extraction |
| BUG-012 | PARTLY FIXED | Text inside HTML tables is dropped from the paragraph list, so it is never translated |
| BUG-013 | OPEN - NEEDS DECISION | Short colloquial Vietnamese dialogue with names and French words is rejected by `is_target_text` |
| BUG-014 | OPEN - NEEDS DECISION | A `<blockquote>` feature box with several `<p>` is translated and paired as one block |
| BUG-015 | OPEN - NEEDS DECISION | Endnote lines with a translated lead phrase and an English citation fail the coverage audit |
| BUG-016 | FIXED | Section-heading entries in `toc.ncx` stay English-only in the bilingual EPUB |
| BUG-017 | FIXED | Nav labels show "(untitled)" as the English side for pages without a heading |
| BUG-018 | OPEN - NEEDS DECISION | Short Vietnamese labels whose words use only shared accented letters fail `is_target_text` |
| BUG-019 | FIXED | Grade check N1 reports false alarms for footnote numbers and decimals |
| BUG-020 | PARTLY FIXED | Grade check JC fails on overlapping and ordinary-word glossary terms |
| BUG-021 | OPEN - NEEDS DECISION | `grade_checks` crashes on Windows when it prints a line with "｜" |
| BUG-022 | FIXED | The `bilingual_coverage_audit.py` command line always audits as zh-tw, so a correct vi book fails |

## BUG-001: EPUBs that pack several chapters into one spine file extract as a few huge items

**STATE: FIXED** (2026-11-12, branch fix/bug-001-ncx-split (DECISION-013, DECISION-014))

**Symptom:** `runs/subtract/subtract.epub` (the table of contents lists about 20 sections) extracts to 5 spine items; the three body items hold 125k, 137k and 198k characters, each spanning several chapters. Alice extracts to 14 one-chapter items.
**Root cause:** `scripts/extract_epub.py` treats the OPF spine as the source of truth and creates one item per spine file; it does not split a file at chapter headings or at the NCX/nav entries. Found by reading the code and the manifest, not yet traced to a failing run.
**Reachability:** Reachable for any EPUB built with split files that group chapters (found with *Subtract*). The subagent translates one spine item per call, so an item of 100k+ characters will not fit in a call; the nav and coverage audits would also see one entry for several chapters. Not hit in Phases 0-3, which use excerpts.
**Options:** (a) split a spine file at the NCX/nav targets or at chapter headings during extraction; (b) a separate pre-step script before extraction; (c) document the limit in `SKILL.md` and require pre-split EPUBs.
**Status:** fix timing agreed 2026-11-11: decide the approach (a, b or c) at the start of Phase 4 and fix before Phase 5 starts. No fix applied yet. Phase 3 uses excerpts of *Subtract* (user, 2026-11-11); this blocks Phase 5 (full book) unless fixed or avoided. Approach decided 2026-11-12: option (a), see DECISION-013; fix lands in its own PR before Phase 5. FIXED 2026-11-12 on branch fix/bug-001-ncx-split (design in 4.6 of the Phase 4 doc; size threshold DECISION-014).

## BUG-002: A vi book whose glossary register matches no hint phrase is audited with min_length_ratio 0.22

**STATE: FIXED** (2026-11-12, Phase 4)

**Symptom:** `_min_length_ratio_from_book_dir` returns the hard-coded 0.22 when no register matches, which is effectively no truncation check for Vietnamese (measured vi/en ratios are 0.80 and up; a half-translated paragraph at 0.45 passes).
**Root cause:** `resolve_register` matches the glossary's free-text `style_anchor.register` against each hint's phrase ("storyteller cadence", "practical business memoir", "scholarly precision"), and the glossary prompt (`scripts/glossary.py:94`) lets the model "invent a new register description"; an invented phrase matches nothing. The default 0.22 was tuned for Chinese. A pinned Phase 2 test (`test_min_length_ratio_for_vi_falls_back_to_the_default`) asserts 0.22 for an unknown register, so changing it needs a decision.
**Reachability:** Reachable whenever the glossary model invents a phrase. Not yet observed in a real run (Phase 5 will show).
**Options:** (a) a top-level `default_min_length_ratio` key in `assets/register_hints.vi.json`, read by `_min_length_ratio_from_book_dir`, no new profile field, and amend the pinned test; (b) constrain the glossary prompt to the registered phrases; (c) a check after the glossary step that `resolve_register` is not None (advice from the Phase 3 Advise call).
**Status:** fix timing agreed 2026-11-11: fix in Phase 4, in code (option a: `default_min_length_ratio` key in `assets/register_hints.vi.json`, amend the pinned Phase 2 test). FIXED 2026-11-12 in Phase 4 (option a; Advise call logged; two pinned vi tests amended). Source: Advise call 3.6 (claims verified in the code).

## BUG-003: The standalone `translation_quality_audit.py` CLI ignores the profile

**STATE: FIXED** (2026-11-12, Phase 4)

**Symptom:** `main()` calls `_min_length_ratio_from_book_dir(args.book_dir)` and `audit_with_warnings(...)` with no profile, so running the script directly on a vi book uses zh-tw hints, the zh-tw target class and the Simplified gate.
**Root cause:** the CLI has no `--target-lang` option and does not read `state.json`. `audit_suite.py` passes the profile, so only direct invocation is affected.
**Reachability:** only by running `python scripts/translation_quality_audit.py` directly on a vi book. Not checked whether `SKILL.md` does that (Phase 4 should check).
**Options:** read `target_lang` from the book dir's `state.json` as `audit_suite` does, or add `--target-lang`.
**Status:** fix timing agreed 2026-11-11: fix in Phase 4 alongside the `SKILL.md` edit (read `target_lang` from `state.json`). FIXED 2026-11-12 in Phase 4 (CLI reads state.json via audit_suite._profile_for_book). `SKILL.md` runs the audits through `audit_suite` but also names `translation_quality_audit.py` directly.

## BUG-004: A dispatch `register_override` changes the prompt but not the audit's length threshold

**STATE: OPEN - NO FIX PLANNED** (revisit only if a real run uses register_override)

**Symptom:** with a `register_override`, the subagent prompt uses the overridden register's rules, but `_min_length_ratio_from_book_dir` still resolves the register from the glossary's `style_anchor`.
**Root cause:** the audit only calls `resolve_register(glossary, ...)`; it has no access to the override. Found by reading the code, not observed in a run.
**Reachability:** only when an override is used and its register has a different ratio from the glossary's. With the flat vi value (0.60 for all registers) it has no effect for vi; for zh-tw the academic register is 0.30 against 0.22.
**Options:** pass the override into the audit, or leave it.
**Status:** no fix scheduled (agreed 2026-11-11). Revisit only if a real run uses `register_override`.

## BUG-005: The coverage audit's failure text says "adjacent zh" for every language

**STATE: FIXED** (2026-11-17, PR #38; failure text only, success line and docstring left)

**Symptom:** For a `vi` book, `bilingual_coverage_audit` reports `missing adjacent zh after: ...` (found in the Phase 4 dry run). The module docstring and the success line ("adjacent Han translations") are also zh-only.
**Root cause:** The message strings in `scripts/bilingual_coverage_audit.py` (lines 1, 75, 201) were never made profile-aware; the logic is. Wording only; the verdict is correct.
**Reachability:** Every failing or passing `vi` run; misleading to a reader, no wrong result.
**Options:** (a) use the profile's `long_name` or code in the messages, keeping the zh-tw text byte-identical; (b) leave as is.
**Status:** logged 2026-11-12, no fix scheduled; needs a decision (the zh-tw wording is pinned by existing tests, so a change must keep it byte-identical). FIXED 2026-11-17 (option a, no profile field): the failure message uses `profile.code.split('-')[0]`, so vi says "missing adjacent vi" and zh-tw stays "missing adjacent zh". Not fixed: the success line and docstring still say Han/zh; they are reachable only through the standalone CLI, which has no `--lang` flag.

## BUG-006: `source_only` items inside a split file are not exempted from the coverage and quality audits

**STATE: FIXED** (2026-11-12, PR #15)

**Symptom:** Phase 5 full-book run: `audit_suite` gives 2 PASS / 2 FAIL (`bilingual_coverage` 603 failure lines, `translation_quality` 598 "source-only paragraph not in exceptions" plus 1 "target too short"). About 99% of the failing paragraphs are endnote citations and tail-page text that the manifest declares `source_only` (`Notes`, `Image Credits`, "Thank you for buying this"); the auto-generated `OEBPS/translations/source_only.json` has only 12 entries, none of them from the `Notes` item.
**Root cause:** (read from the code, not yet confirmed by a fix) `_emit_translations_payload` in `scripts/assemble.py` (lines 326-331) maps each output file to one entry with `entry_by_basename`, keyed by file name; a dict comprehension keeps the last entry per file. After the BUG-001 split several spine items share one file (`index_split_002.html` holds items 014 to 022), so the file is judged by the last entry (a `translate` item), the `manifest_source_only` reason is never applied to the `Notes` paragraphs, and `untranslated_reason` returns no reason for them.
**Reachability:** Any book where a split file holds a `source_only` item next to `translate` items and the source-only item has English paragraphs. Reached on the first real run; the Alice fixtures have no split files.
**Options:** (a) in the payload step, decide the strategy per paragraph by the spine entry (fragment) the paragraph came from, not per file; (b) have the rewriter record exceptions while it rewrites each entry and pass them up; (c) leave as is and translate `Notes` (cost about a sixth of the run) so nothing is source-only.
**Status:** logged 2026-11-12; fix approved by the user the same day and made test-first in PR #15 (`fix/bug-006-split-source-only`, 3 new tests, 671 passed). On the real run the failing lines dropped from about 1,200 to 24. **FIXED** 2026-11-12: PR #15 merged.

## BUG-007: NCX table of contents is mostly English-only for books with split files

**STATE: FIXED** (2026-11-12, PR #17, confirmed on Kindle)

**Symptom:** Phase 5 Kindle read-back (user, 2026-11-12): the table of contents shows one language, not bilingual. In `runs/subtract/subtract_bilingual.epub`, `nav.xhtml` is fully bilingual but `toc.ncx` has 22 labels and only 3 are bilingual.
**Root cause:** (read from the code and confirmed on the output) `patch_toc_ncx` in `scripts/nav_builder.py` matches NCX points to spine entries by file name only. After the BUG-001 split several entries share one file, `_nav_entry_by_filename` keeps the first entry per file, and `patch_toc_ncx` patches only the first fragment point of each file. The other points keep their English text. DECISION-013 listed this as "known and unchecked".
**Reachability:** Any book with split files read in a reader that prefers the NCX (Kindle does). Alice has no split files, so no existing test covers it.
**Options:** (a) key entries by file name plus `fragment_id` and patch every NCX point whose target has a matching entry; (b) regenerate the whole NCX from the same entry list that builds `nav.xhtml`; (c) leave as is and document that Kindle shows the English-only NCX.
**Status:** logged 2026-11-12; fix approved by the user (option a, the smallest change) and made test-first in PR #17. Real run: NCX labels bilingual 3 of 22 before, 21 of 22 after (the book title is the one left). **FIXED** 2026-11-12; user confirmed on Kindle.

## BUG-008: A technical vi book keeps a few English-only labels in the output EPUB

**STATE: PARTLY FIXED** (docTitle fixed; garbled label for a heading-less source TOC page left open on purpose)

**Symptom:** Grade (haiku, 2026-11-12) on the full run of *System Design Interview* (`bt-out/…_bilingual_vi.epub`) failed one rubric line, criterion (e), for metadata only: `titlepage.xhtml` shows the bare English text "Cover" (the Vietnamese profile label is "Bìa"); `toc.ncx` `docTitle` is English-only; one nav label had an English-only gloss ("Data centers ｜ Data center"); and the nav label for the source table-of-contents page is a garbled concatenation ("Table of Contents System Design Interview: An Insider's Guide FOREWORD CHAPTER 1 ｜ Mục lục"). Body paragraphs were not affected.
**Root cause:** (read from the code and the files, 2026-11-12) (1) The title page "Cover" is not a visible defect: `titlepage.xhtml` is an image-only page whose only text is the invisible `<title>Cover</title>`; Grade read it as body text. (2) The garbled TOC label: the source TOC page has no heading tag and its role is `body`, so `extract_epub` falls back to the first words of the page for `first_heading`; classifying it as `contents` would also change its `output_strategy` and which items are translated, so it is left alone. (3) `patch_toc_ncx` never touched the NCX `docTitle`, the leftover noted under BUG-007. (4) The "Data centers" label was our own glossary choice, fixed as book data.
**Reachability:** Any vi book. Cosmetic, in navigation metadata only.
**Options:** (a) fix in the assembler: translate or gloss the title-page text and `docTitle` from the profile's labels or the glossary, and give the source TOC page a profile label instead of its heading text; (b) leave and fix per book through `translations_extra.json`; (c) accept.
**Status:** logged 2026-11-12; user chose the narrow fix on 2026-11-12. `patch_toc_ncx` now appends the profile's bilingual edition label to the NCX `docTitle`, as `nav.xhtml`'s `<title>` already does (test first, `test/test_ncx_doctitle.py`; the zh-tw golden cases have no `docTitle` and are unchanged, but a real zh-tw NCX with a `docTitle` now gets the zh-tw label too). **FIXED** for the `docTitle`. Left open on purpose: the garbled label for a heading-less source TOC page (cosmetic; fixing it risks the zh-tw extraction output); "Cover" is not a defect. The "Data centers" label was changed in this book's `translations_extra.json` only.

## BUG-009: Reference-list and URL paragraphs are not exempted automatically in a vi book

**STATE: CLOSED - DOCUMENTED, NOT FIXED IN CODE** (per-book source_only.json described in SKILL.md; option (c))

**Symptom:** In the first full run of a technical vi book, the coverage and quality audits reported about 320 failure lines, around 150 of them bibliography entries and URL lines that are correctly identical to the English source ("[8] Single point of failure: https://…", chapter 16 lists of articles, blogs and books). The audits only exempt such paragraphs when assembly writes an explicit `{src_text, reason}` entry into `source_only.json`; assembly generated none for these pages.
**Root cause:** unknown. `assemble.py` builds exceptions through `paragraph_classification.untranslated_reason`, which apparently returned no reason for these paragraphs under the vi profile (the `Reference materials` pages exist in the manifest). Not investigated further; worked around by hand.
**Reachability:** Any vi book with a reference section (very likely all non-fiction). Observed once, on this book. No test covers it for vi.
**Options:** (a) find why `untranslated_reason` returns no reason on vi reference pages and fix it, with a test; (b) generate the exception from the manifest heading ("Reference materials", bibliography, notes) in assembly; (c) leave it and require a per-book `translations/source_only.json` (the workaround used: 234 entries generated from the reference pages and URL-only lines, each with a stated reason).
**Status:** logged 2026-11-12; user chose option (c) on 2026-11-12: no code change, document the per-book `translations/source_only.json` in `SKILL.md` (Step 8, "Reference lists on pages with generic file names"). **CLOSED as documented**, not fixed in code; a heading-based exemption was declined because every extra exemption weakens the gate. Revisit if reference pages with generic file names keep appearing. Root cause confirmed by reading `paragraph_classification.untranslated_reason`: it matches only the page file name tokens and CSS classes.

## BUG-010: `state.json` has no protection against concurrent writers

**STATE: FIXED, WITH A LIMIT** (callers that use state.update are safe; plain load + save callers are not)

**Symptom:** Not observed as data loss. In the first full vi run (2026-11-12, *System Design Interview*), up to five subagents each ran a helper that did `state.load` → `mark_done` → `state.save` on the same `state.json` at the same time. At the end all 108 translate items had both a translation file and status `done`, and a mid-run count matched the file count, so no update was lost in that run.
**Root cause:** (read from the code) `state.save` in `scripts/state.py` is `json.dumps(...)` followed by a plain `write_text`: no file lock, no atomic replace and no merge with what is on disk. Two writers whose load-modify-save overlap leave only the last write; a reader that loads during a write can also see a truncated file and fail on invalid JSON. The skill's own flow has the main session call `mark_done` once per returned subagent, which serialises writes. The race was introduced by the run's helper script (`bt_finalize.py`, kept in the session scratchpad, not in the repo), which moved the call into each parallel agent.
**Reachability:** Any run that updates `state.json` from more than one process at once: parallel finalize steps, or the concurrent-chapter option of the translator driver if it saves state from several workers. Not reachable through the documented sequential flow in `SKILL.md`. A lost update would show a finished item as `pending`, so resume would redo it and assembly would fail closed until fixed.
**Options:** (a) hold a file lock around load-modify-save in the helper and write via a temp file and `os.replace`; (b) keep all `state.json` writes in the main session and have subagents only return results, as `SKILL.md` describes; (c) one small state file per item, merged when the run ends; (d) accept it and document that parallel writers are unsupported.
**Status:** logged 2026-11-12; user chose option (a) on 2026-11-12 (atomic write + lock helper). `state.save` now writes a temp file and `os.replace`s it; new `state.update(path, mutate)` takes an exclusive lock (`<name>.lock`, created with `O_EXCL`, portable, stale after 60 s, 30 s timeout), loads, mutates, saves. Test first (`test/test_state_concurrency.py`, six real processes with the spawn start method). Demonstration: the same six-process run without the lock leaves only 8-10 of 48 items marked done (and `PermissionError` crashes on Windows); with `update` all 48 are done. **FIXED** for callers that use `update`; plain `load` + `save` callers are not protected, the run helper is now `scripts/bt_finalize.py` and calls `update`.

## BUG-011: A reply with no `[[PARA_n]]` markers passes `validate_translation` but crashes extraction

**STATE: FIXED, WITH A LIMIT** (bt_finalize.py only; other callers of validate_translation are not protected)

**Symptom:** Found by reading and running `scripts/bt_finalize.py` for the Phase 6 test (2026-11-12), not seen in a book run. A raw reply of two plain paragraphs and no markers makes `validate_translation` return `[]`, then `extract_aligned_translation` raises `ValueError: missing markers ... [1, 2]`. The script exits with a traceback instead of printing `WARNINGS`.
**Root cause:** `dispatch.validate_translation` only checks markers when the reply contains at least one `[[PARA_`; otherwise it takes the legacy paragraph-count branch (`scripts/dispatch.py`, the `else` after the marker check), which passes when the paragraph count is close enough. `extract_aligned_translation` always requires markers. The two checks disagree on what a valid reply is.
**Reachability:** Any subagent reply that drops all markers (a likely model failure). No data is lost: extraction runs before the translation file is written and before `state.update`, so the item stays `pending`. The cost is a traceback instead of a clear warning, and any caller that trusts `validate_translation` alone would go on to crash. Covered for the script by `test_reply_without_markers_exits_1_with_warnings_and_changes_nothing`.
**Options:** (a) in `validate_translation`, warn when the expected reply is marker-aligned but has no markers (changes a shared function; it needs a check against the zh-tw golden cases and the offline path, which may legitimately use the legacy branch); (b) make `bt_finalize.py` catch the `ValueError` and print it as `WARNINGS` (script only, no shared-code risk); (c) leave it.
**Status:** logged 2026-11-12; user chose option (b) on 2026-11-13 ("minimum but effective"). `bt_finalize.py` catches the `ValueError` and prints it as `WARNINGS` with exit 1; test first (`test_reply_without_markers_exits_1_with_warnings_and_changes_nothing`). **FIXED** in the script only. `validate_translation` still passes a marker-less reply, so any other caller that trusts it alone is not protected (option (a) not taken).

## BUG-012: Text inside HTML tables is dropped from the paragraph list, so it is never translated

**STATE: PARTLY FIXED** (extractor warns about table text (b); it still does not translate table cells)

**Symptom:** *Down and Out in Paris and London* (2026-11-13): three short verses sit in `<table class="simplelist">` blocks (item_006, item_028, item_033; six lines in all). `dispatch.html_to_paragraphs` does not return them, so the translators never saw them, and the bilingual EPUB shows them in English only. Every audit passed: the lines are not in the paragraph list, so nothing checks them. A subagent noticed the gap (item_028: "the verse itself is missing from the source").
**Root cause:** not traced into `extract_paragraphs` yet; the check was that no `<td>` text appears in any extracted paragraph for these three items (0 of 6). The tables are verse or lists, not data tables.
**Reachability:** Any EPUB with poetry, lyrics or lists laid out as tables. Silent: no audit sees it.
**Options:** (a) make the extractor return table cell text as paragraphs (touches shared extraction code; needs a zh-tw golden check); (b) detect dropped blocks at extract time and list them for the user; (c) document it and translate such blocks by hand.
**Status:** logged 2026-11-13; user chose 1a + 1b on 2026-11-13. **Partly fixed:** (b) `extract_epub.extract` now prints a stderr warning listing the items and cells whose table text is not extracted (`skipped_table_text`, `test/test_extract_table_warning.py`, test first; manifest and chapters unchanged). The extractor still does not translate table cells (option a not taken). In this book the six lines were translated by hand: `table_cells_vi.json` plus `apply_table_cells.py` in the book folder, applied to the assembled EPUB after every assemble.

## BUG-013: Short colloquial Vietnamese dialogue with names and French words is rejected by `is_target_text`

**STATE: OPEN - NEEDS DECISION** (worked around with 4 source_only.json entries)

**Symptom:** In the same run, the coverage audit failed on 4 correct translations of 50-60 characters, for example “‘Sainte Éloïse?’ Maria nói. ‘Sainte Éloïse là sao?’” (matches 0 of 3 counted words) and “‘Đồ ngu!’ nó kêu lên. ‘Imbecile! Thế còn cái này là gì?’” (1 of about 12).
**Root cause:** the 1-in-5 rule (DECISION-016) counts lowercase-initial tokens; short dialogue made of common Vietnamese words without distinctive letters (nói, là, sao) plus names and French words falls under it. Same class as the three false negatives pinned in `test/test_vi_detector_technical.py`, now seen on narrative text.
**Reachability:** Any vi fiction or memoir with short dialogue lines of 50+ characters. Second book in which a per-book exception was needed for this class.
**Options:** (a) leave it and list the lines in the book's `source_only.json` (done here, 4 entries); (b) revisit the rule (Advise call first, CLAUDE.md trigger 2), for example a floor on the share of tokens with any Vietnamese-distinctive letter or the function-word list; (c) accept it.
**Status:** logged 2026-11-13; waiting for a decision. Worked around with 4 `source_only.json` entries in this book.

## BUG-014: A `<blockquote>` feature box with several `<p>` is translated and paired as one block

**STATE: OPEN - NEEDS DECISION** (no longer a Grade failure since check A2)

**Symptom:** In *Scarcity* (EPUB with `EB20ExtraFeatureLast`/`FeatureIndented` boxes), Grade rubric (a) failed: 49 English paragraphs of 50+ characters in ch1, 3, 5, 7-10 are not tagged `src`. Example: the Shawn box in the Introduction is one `<blockquote class="… src">` holding two `<p>`; the Vietnamese follows as one merged `tgt` paragraph. No text is missing: 0 of these have no Vietnamese after them.
**Root cause:** unknown, likely `content_blocks` treating `blockquote` as one text block (`TEXT_TAGS`) and joining its inner `<p>` text, so `html_to_paragraphs` returns one paragraph per box. Not traced in the code yet.
**Reachability:** Any book with multi-paragraph quote or sidebar boxes inside one `<blockquote>`. The reader sees the box as one English block and one Vietnamese block, not paragraph by paragraph. Possibly acceptable by design.
**Options:** (a) accept it (box = one block); (b) split a blockquote into its inner `<p>` in `content_blocks` (shared code, needs a zh-tw golden check); (c) relax Grade rubric (a) to say "per block".
**Status:** logged 2026-11-13; waiting for a decision. Not fixed in this book. Note 2026-11-14: the new Grade check A2 counts a whole blockquote as one block, so this no longer fails Grade.

## BUG-015: Endnote lines with a translated lead phrase and an English citation fail the coverage audit

**STATE: OPEN - NEEDS DECISION** (worked around with 18 source_only.json entries)

**Symptom:** In *Scarcity* the Notes section (303 paragraphs) failed `bilingual_coverage` on 18 lines such as “23 Một nghiên cứu của nhà tâm lý học Jaime Kurtz : J. L. Kurtz, “Looking to the Future …” (2008): 1238–41. doi:…”; 4 of them also failed `translation_quality` as “target equals source”. The translations are correct.
**Root cause:** the Vietnamese lead phrase is short next to a long English citation, so `is_target_text` (1-in-5 rule, see BUG-013) rejects the whole line; lines whose lead phrase is a proper name or title are identical to the source after the key phrase.
**Reachability:** Any vi book with endnotes that keep citations in the original language (most non-fiction). Third book class after BUG-009 and BUG-013 needing a hand-written `source_only.json`.
**Options:** (a) keep listing them by hand (done here, 18 entries); (b) exempt endnote lines from the Vietnamese-share rule when the lead phrase has Vietnamese; (c) accept it.
**Status:** logged 2026-11-13; waiting for a decision. Worked around with 18 `source_only.json` entries in this book.

## BUG-016: Section-heading entries in `toc.ncx` stay English-only in the bilingual EPUB

**STATE: FIXED** (2026-11-16, PR #29 via #31, vi only)

**Symptom:** In *Scarcity* the output `toc.ncx` has 87 navPoints and 65 of them have no Vietnamese: 64 in-chapter section headings (for example “SLACK”, “TUNNELING”, “THE FOCUS DIVIDEND”) and the second Part One entry (“Part One: THE SCARCITY MINDSET”, same file as the divider page). Grade (second run) reported it under rubric (e). The 22 chapter-level entries are bilingual (“Introduction ｜ Lời nói đầu”). `nav.xhtml` lists only spine-level pages, so it is not affected.
**Root cause:** `nav_builder.patch_toc_ncx` labels only the chapter-level navPoint of each file and skips same-file descendants on purpose (comment: “Same-file descendants are subsection labels”). The Vietnamese heading does exist in the output, directly after the anchor (`<h5 id="sca0000608">SLACK</h5><p class="tgt tgt-vi …">KHOẢNG ĐỆM</p>`), but nothing reads it back into the NCX. Found by reading the code and the NCX; the fragment-matching branch (BUG-007) covers split-file entries only.
**Reachability:** Any book whose source NCX lists in-chapter headings (most non-fiction). Affects only the legacy NCX; EPUB 3 readers use `nav.xhtml`. Pages with no entry in the source NCX (Title Page, brand page, Part Two/Three divider pages, “THE BEGINNING”) are labelled in `nav.xhtml` but cannot be in the NCX without adding entries.
**Options:** (a) for fragment navPoints, take the text of the `tgt` sibling that follows the anchor and write `English ｜ Vietnamese` (shared code, needs a zh-tw golden check); (b) leave the NCX headings English and say so; (c) drop in-chapter entries from the NCX.
**Status:** user chose option (a), Vietnamese only, 2026-11-13. FIXED 2026-11-16: PR #29, landed on main through #31. *Scarcity* NCX: 65 English-only entries before, 2 after (a heading whose translation equals its source, "BENIHANA", and a second whole-file "Part One" entry with no anchor to read from).

## BUG-017: Nav labels show "(untitled)" as the English side for pages without a heading

**STATE: FIXED** (2026-11-16, PR #30 via #31, all languages)

**Symptom:** In *Scarcity* `nav.xhtml` has entries such as "(untitled) ｜ Trang thương hiệu", "(untitled) ｜ Phần I", "(untitled) ｜ Phần II", "(untitled) ｜ Trang cuối" (9 nav/NCX labels in all; found by check E5 of the new Grade rubric). The dedication entry shows its whole first sentence as the English side ("For Amma, Appa, and e3, for and with unconditional love SM For Anastasia, Sophie ｜ Lời đề tặng"). The Vietnamese side is right; the English side is a placeholder or a long text fragment.
**Root cause:** `extract_epub.py:157` falls back to `"(untitled)"` (or the first text of the page) as `first_heading` when a page has no heading tag, and `_nav_display_label` prints `first_heading ｜ label`.
**Reachability:** Any book with image-only brand pages or part divider pages (most trade non-fiction). Cosmetic, navigation only.
**Options:** (a) when the heading is a placeholder, show only the target label; (b) show the profile's English label for known pages (e.g. "Dedication"); (c) accept.
**Status:** logged 2026-11-13. Option (a) chosen for all languages 2026-11-14 (DECISION-018); TASK.md approved the same day. FIXED 2026-11-16: PR #30, landed on main through #31: `_nav_display_label` shows only the target label for a placeholder heading. *Scarcity*: 9 labels with "(untitled)" before, 0 after. Not covered: the dedication entry whose English side is its whole first sentence.

## BUG-018: Short Vietnamese labels whose words use only shared accented letters fail `is_target_text`

**STATE: OPEN - NEEDS DECISION** (not fixed; 305 amber warnings accepted in *The Personal MBA*)

**Symptom:** In *The Personal MBA* `bilingual_coverage` ends WARN, not PASS, with 305 "missing adjacent zh" lines for correct translations. Examples: "Attention" -> "Sự chú ý", "Goals" -> "Mục tiêu", "Habits" -> "Thói quen", "Free" -> "Miễn phí", "Scale" -> "Quy mô". They sit in the Contents page, the Key Terms page and chapter section headings.
**Root cause:** `_vi_is_target_text` counts only lowercase-initial tokens and, for those, only letters that are not shared with French or Portuguese (ú, ý, ó, í, ô, ê and so on). "Sự chú ý" counts ["chú", "ý"], neither matches, so it returns False; "Mục tiêu" -> ["tiêu"] and "Thói quen" -> ["quen"] fail the same way. Checked by calling the function on 8 labels: 7 False, only "Tính đáng chú ý" True (has đ). Same cause family as BUG-013 and BUG-015.
**Reachability:** Any vi book with short heading, term or contents lines. They are amber WARN, not FAIL, so the audit still passes; the Grade checks may count them.
**Options:** (a) accept the warnings; (b) add more function words or count the capitalised first token for short text (changes a detector rule, so an Advise call comes first); (c) list them in `source_only.json` (wrong: they are translated).
**Status:** logged 2026-11-16; waiting for a decision. Not fixed.

## BUG-019: Grade check N1 reports false alarms for footnote numbers and decimals

**STATE: FIXED** (2026-11-16, `scripts/grade_checks.py`, all languages)

**Symptom:** In *The Personal MBA* N1 says NO for 4 blocks whose translations are correct. "$28,650.10" and "$66,300.11" (a footnote number stuck to the figure) are read as the numbers 2865010 and 6630011; "$0.50" becomes "0,5 đô la" and its source token "050" is not found; "2009.9" is read as 20099.
**Root cause:** `_number_tokens` in `scripts/grade_checks.py` strips separators and joins what follows, so a footnote number after a figure becomes part of it, and a decimal point is treated as a separator, not as a decimal mark. Found by printing the 4 pairs (`scripts/grade_checks.py`, N1 block).
**Reachability:** Any book with endnote numbers directly after figures or with decimal amounts (most non-fiction). It turns a correct book into a Grade FAIL.
**Options:** (a) skip a trailing 1–3 digit group that follows a sentence-final figure and compare decimals in both notations; (b) accept N1 as advisory; (c) leave it and review by hand.
**Status:** logged 2026-11-16. FIXED the same day, option chosen by the user: N1 now reads each source block with `<sup class="endnote">` markers removed (`_number_pairs`), and `_plain_number` drops trailing zeros of a decimal part, so "0.50" equals "0,5" and "2,750" equals "2.750" whichever separator the writer used. Tests first: 3 new in `test/test_grade_checks.py`. *The Personal MBA* N1: 4 false alarms before, 0 after. Not fixed here: the model still sees the marker flattened ("28,650.10") and writes "28.650 đô la. 10"; keeping a marker attached needs a change to `content_blocks` (shared with zh-tw).

## BUG-020: Grade check JC fails on overlapping and ordinary-word glossary terms

**STATE: PARTLY FIXED** (glossary fixed for this book; quoted titles fixed in the check; multi-rendering terms open)

**Symptom:** In *The Personal MBA* JC had 4 NO of 20. P0629: "new stock sells out" matched the term "Stock". P2404: "Overhead" matched inside "Communication Overhead", which is correctly rendered "chi phí giao tiếp". P1626: "thay đổi" is in the Vietnamese but the judge said no. P2676: my glossary said Sampling = "Dùng thử" but the book means statistics, so the translation was really wrong in 7 chapter-10 paragraphs, and a part of the real failure.
**Root cause:** the glossary sample lists every term found in the source text, whatever its sense, and overlapping keys (Overhead, Communication Overhead) are both listed. Plain words as keys ("Stock", "Change") match everyday usage. The P2676 case was my wrong glossary entry, not the check.
**Reachability:** Any book whose glossary has plain-word terms or terms inside longer terms.
**More cases (second Grade run, 2026-11-16):** P3031: "Value Stream" inside the English title of an article in an endnote pointer; titles of works stay in English, so the NO is a check limit. P2267: "Management" in an epigraph credit is "QUẢN TRỊ" while the glossary says "Quản lý"; both are valid Vietnamese for "management" depending on context, so one fixed value is too strict (decision: no text change). P2513: the glossary value was "Entropy (độ hỗn loạn)", and the explanatory bracket is not in the translation; fixed in the glossary (now "Entropy").
**Options:** (a) in `sample_pairs`, drop a term when a longer listed term contains it; (b) list only capitalised occurrences; (c) leave it and read each NO; (d) let a glossary term list several accepted renderings and skip terms inside quoted titles.
**Status:** logged 2026-11-16; waiting for a decision on the rest. FIXED 2026-11-16: terms inside a quoted title-like phrase (3+ words, every word of 4+ letters capitalised) are no longer listed for JC (`_strip_quoted_titles`). Open: a term with several valid renderings (Management). Glossary: Sampling set to "Lấy mẫu", Stock and Overhead removed, and 14 uses of "Dùng thử" replaced in the translations.

## BUG-021: `grade_checks` crashes on Windows when it prints a line with "｜"

**STATE: OPEN - NEEDS DECISION** (not fixed; `PYTHONIOENCODING=utf-8` avoids it)

**Symptom:** `python -m scripts.grade_checks ...` on *The Personal MBA* printed A1 to E2, then stopped with `UnicodeEncodeError: 'charmap' codec can't encode character '｜'` at `print(f"{cid}: ...")` (`scripts/grade_checks.py:327`). E3, E4, N1, G1 and E5 never printed, and the exit was not clean.
**Root cause:** On this Windows machine stdout uses cp1252, which has no "｜" (U+FF5C). Check E3 puts a nav title with "｜" into its evidence text, and `print` fails on it. Not yet checked: whether a console set to UTF-8 (`chcp 65001`) or a redirect to a file behaves the same.
**Reachability:** Any bilingual book on a Windows console with a legacy code page, because every nav title and label carries "｜". Not tested on Linux or macOS, where stdout is normally UTF-8; CI runs the tests, not this command line. It cuts the Grade script output short without a pass or fail line, so a run could be read as complete when it is not.
**Options:** (a) in `main`, call `sys.stdout.reconfigure(encoding="utf-8")` before printing; (b) print with `errors="replace"`; (c) leave it and document `PYTHONIOENCODING=utf-8` in `docs/grade-rubric.md`.
**Status:** logged 2026-11-17; waiting for a decision. Not fixed.

## BUG-022: The `bilingual_coverage_audit.py` command line always audits as zh-tw, so a correct vi book fails

**STATE: FIXED** (2026-11-17, PR #41)

**Symptom:** `python -m scripts.bilingual_coverage_audit --source <src.epub> --output <vi_book.epub>` on the finished *The Personal MBA* output prints `bilingual_coverage_audit: FAIL` with 3077 "missing adjacent zh after: ..." lines (checked 2026-11-17). The same book passes in the Grade checks (A1: 0 FAIL lines).
**Root cause:** `main()` takes only `--source` and `--output`, and `audit()` is called without a profile, so it defaults to `ZH_TW`. A Vietnamese sibling is not Han text, so every paragraph counts as untranslated. Found by running the command that `SKILL.md` gives (lines 864-866).
**Reachability:** Any vi book where someone follows the skill's QA step by hand. The verdict is wrong (a false FAIL), not just the wording. The success line and docstring ("Han translations") are also zh-only (left open in BUG-005). Not checked: whether `structural_audit.py` and `translation_quality_audit.py` have the same gap in their command lines.
**Options:** (a) add a `--lang` option (default `zh-tw`, so current zh-tw use is unchanged) and pass `get_profile(...)` to `audit()`; (b) read the language from the book folder (`state.json`) when `--book-dir` is given; (c) leave the code and say in `SKILL.md` that this command line is zh-tw only, pointing vi books to the `audit_suite` run.
**Status:** logged 2026-11-17; waiting for a decision. Not fixed. Recommendation: (b). `translation_quality_audit.py` already works this way (BUG-003): optional `--book-dir`, language from `state.json` through `audit_suite._profile_for_book`. Plan in the PR that fixes it. FIXED 2026-11-17, PR #41 merged (option b): `--book-dir` is optional; the profile comes from state.json `target_lang`; with no `--book-dir`, or no `state.json` in it, the command warns on stderr and audits as zh-tw (the user asked for this warning). The success line names the language (zh-tw text unchanged), and the SKILL.md QA step passes `--book-dir`. *The Personal MBA*: 3077 FAIL lines before, PASS with 0 after. Not covered: a `state.json` that exists but has no `target_lang` is read as zh-tw without a warning (shared `_profile_for_book`, left alone).

<!--
## BUG-001: <short symptom>

**Symptom:**
**Root cause:**
**Reachability:**
**Options:**
**Status:** pending decision
-->
