# Task: Phase 8 — No "(untitled)" English side in nav labels (BUG-017)

Status: approved by the user 2026-11-14 (all languages). Code done on branch `fix/nav-placeholder-labels`; PR, CI and the Grade run are open.

Related: BUG-017 (`docs/BUGS.md`). Evidence: Grade run 5 on *Scarcity* (vi), check E5: 9 nav/NCX labels such as "(untitled) ｜ Phần I".

## Why

A page with no heading (brand page, part divider, last page) gets `first_heading = "(untitled)"` from `extract_epub.py:157`. `_nav_display_label` in `scripts/nav_builder.py:260` then prints `first_heading ｜ label`, so the reader sees a placeholder as the English side. The target label is already right ("Phần I"). Only the English side is wrong.

## Scope

In: `_nav_display_label` in `scripts/nav_builder.py`; check E1 in `scripts/grade_checks.py` and its line in `docs/grade-rubric.md`; tests.
Out: `extract_epub.py` (the placeholder stays as the internal value); the dedication entry that shows a whole first sentence as the English side (E5 does not check it; log it separately if you want it fixed); NCX entries for pages the source NCX never listed.

## Design (draft)

Option (a) of BUG-017. In `_nav_display_label`: if the cleaned `first` is a placeholder (`"(untitled)"`, `"Untitled"`, or empty) and a target label `zh` exists, return `zh` alone. If there is no target label, return `first` as today (no change).

`patch_toc_ncx` builds its chapter labels from the same function, so nav.xhtml and toc.ncx change together.

Check E1 today asks: "equals a profile label, or contains `｜` plus target text". A label that is only a `nav_overrides` value ("Phần I") would then turn E1 to NO. So E1 gets one more accepted case: the label equals a `nav_overrides` value. The rubric line for E1 changes to match.

## Decision

User answer 2026-11-14: apply to every language (DECISION-018). No profile field, so Advise did not fire. zh-tw output changes for the placeholder case only.

## Definition of Done

- [x] Golden record first: run `_nav_display_label` from `main` at `bb0eb35` (`git show bb0eb35:scripts/nav_builder.py`) on synthetic entries (placeholder with label, placeholder without label, normal heading, structural page). Save real output under `test/golden/`.
- [x] A test built from that record fails on the current code for the placeholder-with-label case only.
- [x] Normal headings, structural pages and the placeholder-without-label case stay equal to the golden record.
- [x] Placeholder with a target label returns the target label alone, in nav.xhtml and toc.ncx.
- [x] `grade_checks` E1 accepts a label equal to a `nav_overrides` value; a test plants a bare English label and still gets NO.
- [x] `docs/grade-rubric.md` E1 line updated; `docs/grade-rubric-validation.md` notes the change.
- [x] Real check on *Scarcity*: reassemble, run `grade_checks`; E1 and E5 both YES, no other check changes from YES to NO.
- [ ] `pytest -q` passes; CI green on ubuntu 3.10/3.12 and windows 3.12.
- [x] `docs/DECISIONS.md` entry (scope answer to question 1). BUG-017 marked fixed with the PR. Ledger row updated with the PR link.
- [x] A Grade run after the change; report the result as it is. Result 2026-11-14: script 14/14 YES, J1 pass, J4 pass (1 no), JC FAIL (2 no, "xoay xở" for glossary "xoay xở nhiều việc cùng lúc"). See `docs/grade-rubric-validation.md`.

## Test Plan

- Golden: `PYTHONPATH=. python test/golden/derive_nav_label.py` from the oracle worktree at `bb0eb35` writes `test/golden/golden_nav_label.json`.
- New tests: `pytest -q test/test_nav_placeholder_labels.py`.
- Regression: `pytest -q test/test_nav_builder.py test/test_nav_fixes.py test/test_ncx_doctitle.py test/test_ncx_section_labels.py test/test_grade_checks.py` (all unedited except `test_grade_checks.py`, which gets the new E1 case).
- Full suite: `pytest -q`.
- Real book: `python -m scripts.assemble --book <book_dir> --out <epub>`, then `python -m scripts.grade_checks --source <src.epub> --output <out.epub> --book-dir <book_dir>`.

## Progress notes

- 2026-11-14: drafted, approved (all languages). Golden record from `bb0eb35` (`test/golden/derive_nav_label.py`, `golden_nav_label.json`). Tests red (4 failed, 1 passed), then green. Full suite 748 passed, 269 skipped. *Scarcity*: 14 of 14 script checks YES, E5 0 labels with "(untitled)". Open: judged Grade run, PR, CI, BUG-017 PR link.
- 2026-11-14: Grade run 6 done, overall FAIL on JC (not caused by this task).
- 2026-11-14: user chose to shorten glossary "juggling" to "xoay xở"; JC rerun 20/20; Grade run 6 now PASS overall. Dream not yet run.
