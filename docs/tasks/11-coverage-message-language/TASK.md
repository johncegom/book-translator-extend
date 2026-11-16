# Task: Phase 11 — Coverage audit failure text names the book's language (BUG-005)

Status: done 2026-11-17 (PR #38 merged, `13db0a6`). DoD and Test Plan approved by the user 2026-11-17.

Related: BUG-005 (`docs/BUGS.md`). Side finding, not in scope: the standalone CLI of `bilingual_coverage_audit.py` has no `--lang` flag and always uses zh-tw (log as BUG-022).

## Why

For a `vi` book the audit prints "missing adjacent zh after: ...". The verdict is right; the wording points at the wrong language.

## Scope

In: the failure message at `scripts/bilingual_coverage_audit.py:75`; one new test.
Out: the success line and module docstring (reachable only through the zh-tw-only CLI); any `LanguageProfile` field (so no Advise call); detector rules and thresholds.

## Design

Message becomes `missing adjacent {lang} after: ...` with `lang = profile.code.split("-")[0]`: "zh" for zh-tw (byte-identical), "vi" for vi. No new profile field. Nothing parses this text (grepped `scripts/`).

## Definition of Done

- [x] New test: a vi book with an untranslated English paragraph fails with "missing adjacent vi". It is red on current code, then green.
- [x] The existing zh-tw tests in `test/test_bilingual_coverage_audit.py` (lines 21, 90, 151 pin "missing adjacent zh") are unedited and pass.
- [x] `pytest -q` passes (764 passed, 269 skipped). Full suite on main after merge: 764 passed, 269 skipped. CI ran on main only (run 43935572921), not on the stacked PR.
- [x] BUG-005 is FIXED in the table and in its entry, with the PR link. Ledger row links the PR.

## Test Plan

- `pytest -q test/test_bilingual_coverage_audit.py`
- `pytest -q`

## Progress notes

- 2026-11-17: approved. Branch `fix/bug-005-coverage-message`, stacked on `docs/bug-021-ledger-merged` (PR #37) so the ledger lines do not conflict.
- 2026-11-17: test red (1 failed, 1 passed), fix applied, 764 passed / 269 skipped. PR #38. Open: CI result, merge.
