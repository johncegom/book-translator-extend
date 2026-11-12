# Bug Log

Entry format: symptom, root cause (or "unknown"), reachability, options, status. Logging is not fixing — wait for an explicit decision before applying a fix.

Candidates from the Vietnamese plan, to log only if they actually occur: short-paragraph detection gaps; English text with a single accented letter (e.g. "café") misclassified as Vietnamese.

## BUG-001: EPUBs that pack several chapters into one spine file extract as a few huge items

**Symptom:** `runs/subtract/subtract.epub` (the table of contents lists about 20 sections) extracts to 5 spine items; the three body items hold 125k, 137k and 198k characters, each spanning several chapters. Alice extracts to 14 one-chapter items.
**Root cause:** `scripts/extract_epub.py` treats the OPF spine as the source of truth and creates one item per spine file; it does not split a file at chapter headings or at the NCX/nav entries. Found by reading the code and the manifest, not yet traced to a failing run.
**Reachability:** Reachable for any EPUB built with split files that group chapters (found with *Subtract*). The subagent translates one spine item per call, so an item of 100k+ characters will not fit in a call; the nav and coverage audits would also see one entry for several chapters. Not hit in Phases 0-3, which use excerpts.
**Options:** (a) split a spine file at the NCX/nav targets or at chapter headings during extraction; (b) a separate pre-step script before extraction; (c) document the limit in `SKILL.md` and require pre-split EPUBs.
**Status:** fix timing agreed 2026-11-11: decide the approach (a, b or c) at the start of Phase 4 and fix before Phase 5 starts. No fix applied yet. Phase 3 uses excerpts of *Subtract* (user, 2026-11-11); this blocks Phase 5 (full book) unless fixed or avoided. Approach decided 2026-11-12: option (a), see DECISION-013; fix lands in its own PR before Phase 5. FIXED 2026-11-12 on branch fix/bug-001-ncx-split (design in 4.6 of the Phase 4 doc; size threshold DECISION-014).

## BUG-002: A vi book whose glossary register matches no hint phrase is audited with min_length_ratio 0.22

**Symptom:** `_min_length_ratio_from_book_dir` returns the hard-coded 0.22 when no register matches, which is effectively no truncation check for Vietnamese (measured vi/en ratios are 0.80 and up; a half-translated paragraph at 0.45 passes).
**Root cause:** `resolve_register` matches the glossary's free-text `style_anchor.register` against each hint's phrase ("storyteller cadence", "practical business memoir", "scholarly precision"), and the glossary prompt (`scripts/glossary.py:94`) lets the model "invent a new register description"; an invented phrase matches nothing. The default 0.22 was tuned for Chinese. A pinned Phase 2 test (`test_min_length_ratio_for_vi_falls_back_to_the_default`) asserts 0.22 for an unknown register, so changing it needs a decision.
**Reachability:** Reachable whenever the glossary model invents a phrase. Not yet observed in a real run (Phase 5 will show).
**Options:** (a) a top-level `default_min_length_ratio` key in `assets/register_hints.vi.json`, read by `_min_length_ratio_from_book_dir`, no new profile field, and amend the pinned test; (b) constrain the glossary prompt to the registered phrases; (c) a check after the glossary step that `resolve_register` is not None (advice from the Phase 3 Advise call).
**Status:** fix timing agreed 2026-11-11: fix in Phase 4, in code (option a: `default_min_length_ratio` key in `assets/register_hints.vi.json`, amend the pinned Phase 2 test). FIXED 2026-11-12 in Phase 4 (option a; Advise call logged; two pinned vi tests amended). Source: Advise call 3.6 (claims verified in the code).

## BUG-003: The standalone `translation_quality_audit.py` CLI ignores the profile

**Symptom:** `main()` calls `_min_length_ratio_from_book_dir(args.book_dir)` and `audit_with_warnings(...)` with no profile, so running the script directly on a vi book uses zh-tw hints, the zh-tw target class and the Simplified gate.
**Root cause:** the CLI has no `--target-lang` option and does not read `state.json`. `audit_suite.py` passes the profile, so only direct invocation is affected.
**Reachability:** only by running `python scripts/translation_quality_audit.py` directly on a vi book. Not checked whether `SKILL.md` does that (Phase 4 should check).
**Options:** read `target_lang` from the book dir's `state.json` as `audit_suite` does, or add `--target-lang`.
**Status:** fix timing agreed 2026-11-11: fix in Phase 4 alongside the `SKILL.md` edit (read `target_lang` from `state.json`). FIXED 2026-11-12 in Phase 4 (CLI reads state.json via audit_suite._profile_for_book). `SKILL.md` runs the audits through `audit_suite` but also names `translation_quality_audit.py` directly.

## BUG-004: A dispatch `register_override` changes the prompt but not the audit's length threshold

**Symptom:** with a `register_override`, the subagent prompt uses the overridden register's rules, but `_min_length_ratio_from_book_dir` still resolves the register from the glossary's `style_anchor`.
**Root cause:** the audit only calls `resolve_register(glossary, ...)`; it has no access to the override. Found by reading the code, not observed in a run.
**Reachability:** only when an override is used and its register has a different ratio from the glossary's. With the flat vi value (0.60 for all registers) it has no effect for vi; for zh-tw the academic register is 0.30 against 0.22.
**Options:** pass the override into the audit, or leave it.
**Status:** no fix scheduled (agreed 2026-11-11). Revisit only if a real run uses `register_override`.

## BUG-005: The coverage audit's failure text says "adjacent zh" for every language

**Symptom:** For a `vi` book, `bilingual_coverage_audit` reports `missing adjacent zh after: ...` (found in the Phase 4 dry run). The module docstring and the success line ("adjacent Han translations") are also zh-only.
**Root cause:** The message strings in `scripts/bilingual_coverage_audit.py` (lines 1, 75, 201) were never made profile-aware; the logic is. Wording only; the verdict is correct.
**Reachability:** Every failing or passing `vi` run; misleading to a reader, no wrong result.
**Options:** (a) use the profile's `long_name` or code in the messages, keeping the zh-tw text byte-identical; (b) leave as is.
**Status:** logged 2026-11-12, no fix scheduled; needs a decision (the zh-tw wording is pinned by existing tests, so a change must keep it byte-identical).

## BUG-006: `source_only` items inside a split file are not exempted from the coverage and quality audits

**Symptom:** Phase 5 full-book run: `audit_suite` gives 2 PASS / 2 FAIL (`bilingual_coverage` 603 failure lines, `translation_quality` 598 "source-only paragraph not in exceptions" plus 1 "target too short"). About 99% of the failing paragraphs are endnote citations and tail-page text that the manifest declares `source_only` (`Notes`, `Image Credits`, "Thank you for buying this"); the auto-generated `OEBPS/translations/source_only.json` has only 12 entries, none of them from the `Notes` item.
**Root cause:** (read from the code, not yet confirmed by a fix) `_emit_translations_payload` in `scripts/assemble.py` (lines 326-331) maps each output file to one entry with `entry_by_basename`, keyed by file name; a dict comprehension keeps the last entry per file. After the BUG-001 split several spine items share one file (`index_split_002.html` holds items 014 to 022), so the file is judged by the last entry (a `translate` item), the `manifest_source_only` reason is never applied to the `Notes` paragraphs, and `untranslated_reason` returns no reason for them.
**Reachability:** Any book where a split file holds a `source_only` item next to `translate` items and the source-only item has English paragraphs. Reached on the first real run; the Alice fixtures have no split files.
**Options:** (a) in the payload step, decide the strategy per paragraph by the spine entry (fragment) the paragraph came from, not per file; (b) have the rewriter record exceptions while it rewrites each entry and pass them up; (c) leave as is and translate `Notes` (cost about a sixth of the run) so nothing is source-only.
**Status:** logged 2026-11-12; fix approved by the user the same day and made test-first in PR #15 (`fix/bug-006-split-source-only`, 3 new tests, 671 passed). On the real run the failing lines dropped from about 1,200 to 24. **FIXED** 2026-11-12: PR #15 merged.

## BUG-007: NCX table of contents is mostly English-only for books with split files

**Symptom:** Phase 5 Kindle read-back (user, 2026-11-12): the table of contents shows one language, not bilingual. In `runs/subtract/subtract_bilingual.epub`, `nav.xhtml` is fully bilingual but `toc.ncx` has 22 labels and only 3 are bilingual.
**Root cause:** (read from the code and confirmed on the output) `patch_toc_ncx` in `scripts/nav_builder.py` matches NCX points to spine entries by file name only. After the BUG-001 split several entries share one file, `_nav_entry_by_filename` keeps the first entry per file, and `patch_toc_ncx` patches only the first fragment point of each file. The other points keep their English text. DECISION-013 listed this as "known and unchecked".
**Reachability:** Any book with split files read in a reader that prefers the NCX (Kindle does). Alice has no split files, so no existing test covers it.
**Options:** (a) key entries by file name plus `fragment_id` and patch every NCX point whose target has a matching entry; (b) regenerate the whole NCX from the same entry list that builds `nav.xhtml`; (c) leave as is and document that Kindle shows the English-only NCX.
**Status:** logged 2026-11-12; fix approved by the user (option a, the smallest change) and made test-first in PR #17. Real run: NCX labels bilingual 3 of 22 before, 21 of 22 after (the book title is the one left). **FIXED** 2026-11-12; user confirmed on Kindle.

## BUG-008: A technical vi book keeps a few English-only labels in the output EPUB

**Symptom:** Grade (haiku, 2026-11-12) on the full run of *System Design Interview* (`bt-out/…_bilingual_vi.epub`) failed one rubric line, criterion (e), for metadata only: `titlepage.xhtml` shows the bare English text "Cover" (the Vietnamese profile label is "Bìa"); `toc.ncx` `docTitle` is English-only; one nav label had an English-only gloss ("Data centers ｜ Data center"); and the nav label for the source table-of-contents page is a garbled concatenation ("Table of Contents System Design Interview: An Insider's Guide FOREWORD CHAPTER 1 ｜ Mục lục"). Body paragraphs were not affected.
**Root cause:** unknown for the title page "Cover" text and the garbled label (not investigated; the title-page item is a `source_only` image page and the garbled label looks like the manifest `first_heading` of the source TOC page being used verbatim). The `docTitle` is the leftover already noted under BUG-007 ("the book title is the one left"). The "Data centers" label was our own glossary choice, fixed as book data.
**Reachability:** Any vi book. Cosmetic, in navigation metadata only.
**Options:** (a) fix in the assembler: translate or gloss the title-page text and `docTitle` from the profile's labels or the glossary, and give the source TOC page a profile label instead of its heading text; (b) leave and fix per book through `translations_extra.json`; (c) accept.
**Status:** logged 2026-11-12; waiting for a decision. Not fixed in the skill. The "Data centers" label was changed in this book's `translations_extra.json` only.

## BUG-009: Reference-list and URL paragraphs are not exempted automatically in a vi book

**Symptom:** In the first full run of a technical vi book, the coverage and quality audits reported about 320 failure lines, around 150 of them bibliography entries and URL lines that are correctly identical to the English source ("[8] Single point of failure: https://…", chapter 16 lists of articles, blogs and books). The audits only exempt such paragraphs when assembly writes an explicit `{src_text, reason}` entry into `source_only.json`; assembly generated none for these pages.
**Root cause:** unknown. `assemble.py` builds exceptions through `paragraph_classification.untranslated_reason`, which apparently returned no reason for these paragraphs under the vi profile (the `Reference materials` pages exist in the manifest). Not investigated further; worked around by hand.
**Reachability:** Any vi book with a reference section (very likely all non-fiction). Observed once, on this book. No test covers it for vi.
**Options:** (a) find why `untranslated_reason` returns no reason on vi reference pages and fix it, with a test; (b) generate the exception from the manifest heading ("Reference materials", bibliography, notes) in assembly; (c) leave it and require a per-book `translations/source_only.json` (the workaround used: 234 entries generated from the reference pages and URL-only lines, each with a stated reason).
**Status:** logged 2026-11-12; waiting for a decision. Not fixed in the skill. Worked around with a per-book `translations/source_only.json`.

<!--
## BUG-001: <short symptom>

**Symptom:**
**Root cause:**
**Reachability:**
**Options:**
**Status:** pending decision
-->
