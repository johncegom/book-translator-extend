# Task: Phase 12 — Coverage audit command line picks the language from the book folder (BUG-022)

Status: in progress. Plan approved by the user 2026-11-17, with one answer: warn when there is no `state.json`.

Related: BUG-022, BUG-005 (left the success line open), BUG-003 (the pattern to copy).

## Why

`python -m scripts.bilingual_coverage_audit` always audits as zh-tw. On the finished vi book *The Personal MBA* it prints FAIL with 3077 false lines, while the Grade check A1 and `audit_suite` pass the same book.

## Scope

In: `main()` of `scripts/bilingual_coverage_audit.py` (new optional `--book-dir`, a warning, a profile-aware success line); the QA snippet in `SKILL.md` (lines 864-872); tests.
Out: `translation_quality_audit.py` (it already has `--book-dir`; it does not warn when the folder has no `state.json`, left as is); `structural_audit.py` and `href_resolve_audit.py` (no profile use found in them; to confirm by reading); any `LanguageProfile` field (no Advise call); detector rules.

## Design

- `--book-dir` is optional. With it, the profile comes from `audit_suite._profile_for_book` (state.json `target_lang`). A code with no profile raises `ValueError`, the same as `translation_quality_audit`.
- Warning on stderr, once, when the language cannot be read: no `--book-dir`, or `--book-dir` without a `state.json`. Text says the audit uses zh-tw and how to change it. The verdict and exit code are not changed by the warning. `_profile_for_book` itself is shared and is not touched.
- Success line: zh-tw keeps "adjacent Han translations" byte-identical; other profiles say "adjacent translations (<long_name>)".

## Definition of Done

- [x] Tests first, seen red: vi book passes with `--book-dir`; no `--book-dir` warns on stderr; `--book-dir` without `state.json` warns; unregistered `target_lang` raises `ValueError`; zh-tw success line unchanged.
- [ ] Existing tests are unedited and pass; `pytest -q` passes (769 passed, 269 skipped: done); CI green on ubuntu 3.10/3.12 and windows 3.12 (pending on PR #41).
- [x] Real check on *The Personal MBA* with `--book-dir`: PASS or WARN like Grade A1, not 3077 FAIL lines.
- [x] `SKILL.md` QA snippet passes `--book-dir` to the coverage and quality audits.
- [x] BUG-022 is FIXED ON BRANCH in the table and the entry, with the PR link. Ledger row links the PR.

## Test Plan

- `pytest -q test/test_coverage_cli_language.py`
- `pytest -q test/test_bilingual_coverage_audit.py` (unedited)
- `pytest -q`
- Real book: `python -m scripts.bilingual_coverage_audit --source <src.epub> --output <vi.epub> --book-dir <book_dir>`

## Progress notes

- 2026-11-17: approved. Branch `fix/bug-022-coverage-cli-book-dir`, built on the open PR #40 branch (BUG-022 text not on main yet); PR goes to main.
- 2026-11-17: 5 new tests red, then green; 769 passed / 269 skipped. *The Personal MBA* with `--book-dir`: PASS, 0 missing lines (was 3077). PR #41. Open: CI, merge. A stray runtime log was committed and then removed in a later commit.
