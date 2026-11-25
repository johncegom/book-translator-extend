# Task: Phase 14 — Translate text inside HTML tables (BUG-012 option a)

Status: approved 2026-11-26, not started. Design A chosen by the user 2026-11-26.

Related: BUG-012 (extractor drops table cell text; option b, the extract warning, is already merged). DECISION entry to add.

## Why

*Down and Out in Paris and London* has three verses in `<table class="simplelist">` (six lines). The extractor never returned them, every audit passed, and they stayed English. They were translated by hand (`table_cells_vi.json` plus `apply_table_cells.py`). The cause is that `content_blocks.TEXT_TAGS` has no `td` or `th`, and dispatch, assembly and the audits all use that one walker.

## Scope

In: `scripts/content_blocks.py` (cells as text blocks, with guards); `scripts/bilingual_rewriter.py` (where a cell translation is inserted); `scripts/bilingual_coverage_audit.py` (where the audit looks for it); `scripts/extract_epub.py` (`skipped_table_text` narrows to what is still skipped); new tests; DECISIONS entry; docs.
Out: the detector and every threshold; `nav_builder`; the hand-made `apply_table_cells.py` in existing book folders (they keep working, they are not migrated).

## Design (Design A)

1. **Walker:** `td` and `th` join the text tags. A cell is a text block only when it has at least one letter and holds no `p`, `li`, `blockquote`, `pre`, `dt` or `dd` (those keep their own handling). `translate="no"` still wins.
2. **Insert:** for a cell, the translation is appended inside the cell as `<p class="tgt ...">`, not inserted after it. Inserting after a `td` would put a `<p>` inside `<tr>`, which is invalid HTML.
3. **Audit:** for a cell, look for the `p.tgt` inside it, not at the next sibling.
4. **Warning:** the extract warning stays for table text that is still skipped (cells with no letters are not listed).
5. **Known limit, to put in DECISIONS:** a data table with words in its cells is now translated cell by cell. Short cells may show as short-line warnings.
6. **Mid-run books:** the paragraph list of a chapter with a table changes. Re-extract an unfinished book before resuming it. Finished books are not affected.

## Definition of Done

- [ ] Ground truth first: paragraph lists of 3 non-table chapters from `git show bb0eb35:scripts/content_blocks.py` are recorded as golden cases; the new code matches them exactly.
- [ ] Tests first, seen red: (a) verse table gives one paragraph per cell; (b) number-only or symbol-only cells give none; (c) `<td><p>text</p></td>` gives one paragraph, not two; (d) `td translate="no"` gives none; (e) the rewriter puts `p.tgt` inside the `td`, never as a child of `tr`; (f) coverage audit passes when the cell has a translation and fails when it has none; (g) a table-free chapter gives output identical to before.
- [ ] Existing tests are unedited and pass; `pytest -q` passes. CI green on main after merge.
- [ ] Real check on *Down and Out* (source `D:\E-Books\epub\orwell-down-and-out-in-paris-and-london.epub`, book folder `D:\E-Books\translations\orwell-down-and-out-in-paris-and-london`): re-extract to a new empty folder, the six verse lines appear as paragraphs; after translating only those, the assembled EPUB shows Vietnamese inside the table cells with no `apply_table_cells.py` step; `bilingual_coverage_audit --book-dir` has no table failure. The existing book folder and EPUB are not overwritten.
- [ ] `zh-tw` output for a book without tables is identical to `bb0eb35`.
- [ ] `docs/DECISIONS.md` entry; BUG-012 updated (FIXED, with the limit from item 5 if it holds); ledger row links the PR.

## Test Plan

- `git show bb0eb35:scripts/content_blocks.py` in a scratch worktree to record the golden paragraph lists.
- `pytest -q test/test_content_blocks.py test/test_extract_table_warning.py` (new cases added)
- `pytest -q test/test_bilingual_rewriter.py test/test_bilingual_coverage_audit.py`
- `pytest -q`
- Real check: `python -m scripts.extract_epub` on the source EPUB into an empty folder, then compare paragraph counts of item_006, item_028 and item_033 with the old extract (BUG-012 lists them).

## Program design

Files touched: `content_blocks.py` (walker), `bilingual_rewriter.py` (insert), `bilingual_coverage_audit.py` (look-up), `extract_epub.py` (skipped list). One shared predicate, `is_cell_text_block(node)`, in `content_blocks.py` is used by all three so the rule lives in one place.

## Sub-tasks

- [ ] Record golden cases from `bb0eb35`
- [ ] Write tests, see red
- [ ] Walker and predicate
- [ ] Rewriter insert
- [ ] Audit look-up
- [ ] Narrow the extract warning
- [ ] Real check on *Down and Out*
- [ ] DECISIONS, BUGS, ledger

## Progress notes

- 2026-11-26: plan drafted. Findings: no table exists in any golden or fixture file (only `test/test_extract_table_warning.py`), so the oracle cases cannot catch a regression here; the real-book comparison above covers it.
