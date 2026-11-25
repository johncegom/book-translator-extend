# Task: Phase 14 — Table text warning at the audit gate (BUG-012 detection)

Status: approved 2026-11-26, not started. Decisions from the user 2026-11-26: a 5th audit in `audit_suite`; WARN only (no Grade check); the earlier code fix is dropped.

Related: BUG-012 (closed 2026-11-20 as documented; the code fix was declined). This phase does not translate table cells. It makes the gap visible at the audit gate, where today every audit passes.

Folder name `14-html-table-text` is kept from the first draft so the ledger link stays valid.

## Why

Table cells with bare text are never extracted, so they are never translated and no audit sees them. The only guard is a stderr warning during `extract_epub`, printed once and easy to miss. After assembly all audits pass. A book can ship with English verse or list items in it and nothing says so.

## Scope

In: new `scripts/table_text_audit.py` (`run(output, book_dir) -> AuditResult`, name `table_text`); one line in `audit_suite.run_all` (appended as the 5th result); new tests; one edit to an existing test (below); SKILL.md Step 7 and Step 8 text; BUG-012 note; DECISIONS entry; ledger.
Out: the walker (`content_blocks.py`), the rewriter, every other audit, `grade_checks` and the Grade rubric (WARN only, decided), any translation of table cells.

## Design

1. Read `<book_dir>/manifest.json`. For each spine item with `output_strategy == "translate"`, read the chapter HTML that extraction wrote, `<book_dir>/<href>` (for example `chapters/item_006.html`). This is the same input the extract warning used, so split files need no special handling. Checked 2026-11-26 on the *Down and Out* folder: `chapters/` exists with 82 files and the manifest `href` values point into it.
2. Find skipped cells with the existing `extract_epub.skipped_table_text`, so the audit and the extract warning always agree.
3. A skipped cell is handled when its text is in `translations/source_only.json` (the same exceptions the coverage audit reads from the output EPUB), or when the output EPUB has a `td`/`th` with that text whose row is followed by a row with class `tgt` (what the hand method `apply_table_cells.py` writes).
4. Result: `pass` when every skipped cell is handled; `warn` otherwise, listing item, file and the first few cells, with `details` holding the counts. Never `fail`. If `manifest.json` cannot be read, or a translate item's chapter file is missing, the result is `warn` with "not checked: <reason>", never a silent pass.
5. Known limit, for DECISIONS: a cell next to an image is skipped by the extractor and is reported too, which is correct. A table that sits only on a `source_only` item is not checked, the same as the extract warning.

## Definition of Done

- [ ] Tests first, seen red: (a) source with bare-text cells and an output with no handling gives `warn` naming item and cell; (b) the same cells listed in `source_only.json` give `pass`; (c) the same cells followed by a `tgt` row in the output give `pass`; (d) a source with no tables gives `pass`; (e) a source whose table cells hold `<p>` gives `pass` (already extracted); (f) a table only on a `source_only` item gives `pass`; (g) missing `manifest.json`, or a missing chapter file, gives `warn` "not checked"; (h) `run_all` returns the new result last, and `format_summary` counts it.
- [ ] One existing test is edited, and only for the count: `test/test_audit_suite.py::test_run_all_orders_and_aggregates_animal_farm` expects 5 names (new one last) and `5 PASS`. Every other existing test is unedited and passes.
- [ ] `pytest -q` passes. CI green on main after the merge.
- [ ] Real check on the four finished vi books with `python -m scripts.audit_suite --source <src.epub> --output <vi.epub> --book-dir <book>`: *Down and Out* (hand step applied) gives `table_text: PASS`; the same book with its hand-added rows removed from a scratch copy gives `WARN` naming the six cells; the other three give `PASS` (no skipped cells, measured 2026-11-20). Results are shown as real output.
- [ ] SKILL.md: Step 8 says 5 audits; Step 7 says where the audit reports table cells. `docs/BUGS.md` BUG-012 stays CLOSED and gets one line naming this phase and the Alice finding (a contents table with bare cells). DECISIONS entry (WARN not FAIL, no Grade check, the code fix built and dropped, with the reasons). Ledger row links the PR.

## Test Plan

- `pytest -q test/test_table_text_audit.py` (new)
- `pytest -q test/test_audit_suite.py test/test_grade_checks.py test/test_lang_profile_vi.py`
- `pytest -q`
- Real check, per book: `python -m scripts.audit_suite --source "<src.epub>" --output "<vi.epub>" --book-dir "<book folder>"` for the four books under `D:\E-Books\translations`, sources under `D:\E-Books\epub` (the source is still a required argument of the command). The existing book folders and EPUBs are read only; the "hand rows removed" case uses a copy in a scratch folder.

## Program design

One new file (`table_text_audit.py`, about 80 lines): `run()` plus two helpers (`_skipped_cells(book_dir, manifest)`, `_handled(output, source_only)`). `audit_suite.run_all` gets one more list item. No change to shared extraction code.

## Sub-tasks

- [ ] Write tests, see red
- [ ] `table_text_audit.py`
- [ ] Wire into `run_all`; edit the one count test
- [ ] Real check on the four books
- [ ] SKILL.md, BUG-012 note, DECISIONS, ledger

## Progress notes

- 2026-11-26: first draft was a code fix (cells as text blocks). Built, tested (797 passed) and oracle-checked on table-free chapters, then dropped by the user in favour of a warning. Reasons recorded for DECISIONS: how a real reader draws a `<p>` inside a `<td>` was not checked, a resumed half-translated book could pair translations with the wrong paragraphs, and the 2026-11-20 measurement said 6 lines in one of four books.
