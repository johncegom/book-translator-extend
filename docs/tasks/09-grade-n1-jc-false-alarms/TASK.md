# Task: Phase 9 — Grade checks N1 and JC false alarms (BUG-019, BUG-020)

Status: done 2026-11-17 (PR #33 open, CI green, not yet merged). This doc was written after the code.

Related: BUG-019 (fixed), BUG-020 (partly fixed), BUG-018 (logged only, not part of this phase). Evidence: Grade runs on *The Personal MBA* (vi).

## Why

Check N1 said NO for 4 correct blocks (footnote numbers stuck to figures, decimal notation). JC listed glossary terms found inside titles of works, which stay in English by design.

## Scope

In: `_number_tokens`, `_number_pairs`, `_plain_number`, `_strip_quoted_titles` in `scripts/grade_checks.py`; tests in `test/test_grade_checks.py`; `docs/BUGS.md` entries BUG-018 to BUG-020.
Out: `content_blocks` (shared with zh-tw; the marker is still flattened for the model); terms with several valid renderings (BUG-020, open); BUG-018 (detector rule, needs an Advise call and a decision).

## Definition of Done

- [x] N1 ignores `<sup class="endnote">` markers in the source and treats "0.50" and "0,5" as equal; "2,750" equals "2.750".
- [x] JC does not list a term inside a quoted title-like phrase (3+ words, every 4+ letter word capitalised).
- [x] Tests for both exist and pass (3 new for N1).
- [x] *The Personal MBA* N1: 0 false alarms (was 4). Rerun 2026-11-17: `N1: YES - 3223 blocks, 0 with a source number missing`; all 14 script checks YES.
- [x] `pytest -q` passes (753 passed, 269 skipped); CI run 43896241718 green on ubuntu 3.10/3.12 and windows 3.12.
- [x] Ledger Evidence cell links the PR.

## Test Plan

- `pytest -q test/test_grade_checks.py`
- `pytest -q`
- Real book: `python -m scripts.grade_checks --source <src.epub> --output <out.epub> --book-dir <book_dir>`

## Progress notes

- 2026-11-16: code and 20 related tests done (run with the font tests). Full suite and CI not yet run.
- 2026-11-17: full suite 753 passed / 269 skipped; CI green. Open: the *The Personal MBA* N1 recheck (0 false alarms). The book is not in this checkout, so only the BUG-019 log (4 before, 0 after) supports it; needs a rerun with the book path.
- 2026-11-17: real-book rerun on *The Personal MBA*: 14 of 14 script checks YES, N1 0 false alarms. Printing needs `PYTHONIOENCODING=utf-8` on Windows (cp1252 crashes on the ｜ character); not fixed here.
