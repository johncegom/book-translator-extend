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
| BUG-005 | OPEN - NEEDS DECISION | The coverage audit's failure text says "adjacent zh" for every language |
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
| BUG-016 | FIXED ON BRANCH, NOT MERGED | Section-heading entries in `toc.ncx` stay English-only in the bilingual EPUB |
| BUG-017 | FIXED ON BRANCH, NOT MERGED | Nav labels show "(untitled)" as the English side for pages without a heading |

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

**STATE: OPEN - NEEDS DECISION** (zh-tw wording is pinned by tests)

**Symptom:** For a `vi` book, `bilingual_coverage_audit` reports `missing adjacent zh after: ...` (found in the Phase 4 dry run). The module docstring and the success line ("adjacent Han translations") are also zh-only.
**Root cause:** The message strings in `scripts/bilingual_coverage_audit.py` (lines 1, 75, 201) were never made profile-aware; the logic is. Wording only; the verdict is correct.
**Reachability:** Every failing or passing `vi` run; misleading to a reader, no wrong result.
**Options:** (a) use the profile's `long_name` or code in the messages, keeping the zh-tw text byte-identical; (b) leave as is.
**Status:** logged 2026-11-12, no fix scheduled; needs a decision (the zh-tw wording is pinned by existing tests, so a change must keep it byte-identical).

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

**STATE: FIXED ON BRANCH, NOT MERGED** (fix/ncx-section-labels, vi only; PR link goes here)

**Symptom:** In *Scarcity* the output `toc.ncx` has 87 navPoints and 65 of them have no Vietnamese: 64 in-chapter section headings (for example “SLACK”, “TUNNELING”, “THE FOCUS DIVIDEND”) and the second Part One entry (“Part One: THE SCARCITY MINDSET”, same file as the divider page). Grade (second run) reported it under rubric (e). The 22 chapter-level entries are bilingual (“Introduction ｜ Lời nói đầu”). `nav.xhtml` lists only spine-level pages, so it is not affected.
**Root cause:** `nav_builder.patch_toc_ncx` labels only the chapter-level navPoint of each file and skips same-file descendants on purpose (comment: “Same-file descendants are subsection labels”). The Vietnamese heading does exist in the output, directly after the anchor (`<h5 id="sca0000608">SLACK</h5><p class="tgt tgt-vi …">KHOẢNG ĐỆM</p>`), but nothing reads it back into the NCX. Found by reading the code and the NCX; the fragment-matching branch (BUG-007) covers split-file entries only.
**Reachability:** Any book whose source NCX lists in-chapter headings (most non-fiction). Affects only the legacy NCX; EPUB 3 readers use `nav.xhtml`. Pages with no entry in the source NCX (Title Page, brand page, Part Two/Three divider pages, “THE BEGINNING”) are labelled in `nav.xhtml` but cannot be in the NCX without adding entries.
**Options:** (a) for fragment navPoints, take the text of the `tgt` sibling that follows the anchor and write `English ｜ Vietnamese` (shared code, needs a zh-tw golden check); (b) leave the NCX headings English and say so; (c) drop in-chapter entries from the NCX.
**Status:** user chose option (a), Vietnamese only, 2026-11-13. Fixed on branch `fix/ncx-section-labels` (not yet merged; PR link goes here). *Scarcity* NCX: 65 English-only entries before, 2 after (a heading whose translation equals its source, "BENIHANA", and a second whole-file "Part One" entry with no anchor to read from).

## BUG-017: Nav labels show "(untitled)" as the English side for pages without a heading

**STATE: FIXED ON BRANCH, NOT MERGED** (fix/nav-placeholder-labels, all languages; PR link goes here)

**Symptom:** In *Scarcity* `nav.xhtml` has entries such as "(untitled) ｜ Trang thương hiệu", "(untitled) ｜ Phần I", "(untitled) ｜ Phần II", "(untitled) ｜ Trang cuối" (9 nav/NCX labels in all; found by check E5 of the new Grade rubric). The dedication entry shows its whole first sentence as the English side ("For Amma, Appa, and e3, for and with unconditional love SM For Anastasia, Sophie ｜ Lời đề tặng"). The Vietnamese side is right; the English side is a placeholder or a long text fragment.
**Root cause:** `extract_epub.py:157` falls back to `"(untitled)"` (or the first text of the page) as `first_heading` when a page has no heading tag, and `_nav_display_label` prints `first_heading ｜ label`.
**Reachability:** Any book with image-only brand pages or part divider pages (most trade non-fiction). Cosmetic, navigation only.
**Options:** (a) when the heading is a placeholder, show only the target label; (b) show the profile's English label for known pages (e.g. "Dedication"); (c) accept.
**Status:** logged 2026-11-13. Option (a) chosen for all languages 2026-11-14 (DECISION-018); TASK.md approved the same day. Fixed on branch `fix/nav-placeholder-labels` (not yet merged; PR link goes here): `_nav_display_label` shows only the target label for a placeholder heading. *Scarcity*: 9 labels with "(untitled)" before, 0 after. Not covered: the dedication entry whose English side is its whole first sentence.

<!--
## BUG-001: <short symptom>

**Symptom:**
**Root cause:**
**Reachability:**
**Options:**
**Status:** pending decision
-->
